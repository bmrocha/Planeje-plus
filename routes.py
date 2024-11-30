from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from datetime import datetime
from models import db, User, Budget, EmailConfig
from forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_mail import Message
from extensions import mail
from app import app
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

def send_notification_email(subject, recipient, body):
    try:
        msg = Message(subject,
                     sender=app.config['MAIL_USERNAME'],
                     recipients=[recipient])
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'administrador':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Sua conta está desativada. Entre em contato com o administrador.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user)
            if user.role == 'administrador':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Email ou senha inválidos', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    budgets = []
    if current_user.role == 'solicitante':
        budgets = Budget.query.filter_by(solicitante_id=current_user.id).all()
    elif current_user.role == 'aprovador':
        budgets = Budget.query.filter_by(aprovador_id=current_user.id, status='pendente').all()
    elif current_user.role == 'administrador':
        budgets = Budget.query.all()
        users = User.query.all()
        
        # Get user statistics
        total_users = len(users)
        solicitantes = sum(1 for u in users if u.role == 'solicitante')
        aprovadores = sum(1 for u in users if u.role == 'aprovador')
        administradores = sum(1 for u in users if u.role == 'administrador')
        
        # Get budget statistics for the current user
        user_pendente = sum(1 for b in budgets if b.solicitante_id == current_user.id and b.status == 'pendente')
        user_aprovado = sum(1 for b in budgets if b.solicitante_id == current_user.id and b.status == 'aprovado')
        user_rejeitado = sum(1 for b in budgets if b.solicitante_id == current_user.id and b.status == 'rejeitado')
        
        return render_template('admin_dashboard.html',
                             budgets=budgets,
                             users=users,
                             total_users=total_users,
                             solicitantes=solicitantes,
                             aprovadores=aprovadores,
                             administradores=administradores,
                             user_pendente=user_pendente,
                             user_aprovado=user_aprovado,
                             user_rejeitado=user_rejeitado)
    
    return render_template('dashboard.html', budgets=budgets)

@app.route('/new_budget', methods=['GET', 'POST'])
@login_required
def new_budget():
    if request.method == 'POST':
        try:
            # Obter dados básicos do orçamento
            title = request.form['title']
            description = request.form['description']
            requested_name = request.form['requested_name']
            sector = request.form['sector']

            # Criar o orçamento
            budget = Budget(
                title=title,
                description=description,
                requested_name=requested_name,
                sector=sector,
                solicitante_id=current_user.id,
                aprovador_id=1  # ID do aprovador padrão
            )
            db.session.add(budget)
            db.session.flush()  # Para obter o ID do orçamento

            # Processar empresas e anexos
            company_names = request.form.getlist('companies[][name]')
            company_files = request.files.getlist('companies[][attachment]')

            for i, (name, file) in enumerate(zip(company_names, company_files)):
                if name:
                    company = Company(name=name, budget_id=budget.id)
                    
                    if file and file.filename:
                        filename = secure_filename(f"budget_{budget.id}_company_{i}_{file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        company.attachment_filename = filename
                        company.attachment_path = filepath

                    db.session.add(company)

            db.session.commit()
            flash('Solicitação criada com sucesso!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar solicitação: {str(e)}', 'error')
            return redirect(url_for('new_budget'))

    # GET request
    sectors = Sector.query.order_by(Sector.name).all()
    return render_template('new_budget.html', sectors=sectors)

@app.route('/create_sector', methods=['POST'])
@login_required
def create_sector():
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'error': 'Nome do setor é obrigatório'})

        # Verificar se o setor já existe
        existing_sector = Sector.query.filter_by(name=name).first()
        if existing_sector:
            return jsonify({'success': False, 'error': 'Setor já existe'})

        # Criar novo setor
        sector = Sector(name=name)
        db.session.add(sector)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'administrador':
        flash('Acesso negado. Você não tem permissão para cadastrar usuários.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        contact = request.form['contact']
        is_active = 'is_active' in request.form
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado. Por favor, use outro email.', 'danger')
            return redirect(url_for('register'))
        
        try:
            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password),
                role=role,
                contact=contact,
                is_active=is_active
            )
            db.session.add(user)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar usuário. Por favor, tente novamente.', 'danger')
            print(str(e))
    
    return render_template('register.html')

@app.route('/budget/<int:id>')
@login_required
def view_budget(id):
    budget = Budget.query.get_or_404(id)
    if current_user.role == 'aprovador' and budget.aprovador_id != current_user.id:
        flash('Você só pode visualizar orçamentos designados a você', 'danger')
        return redirect(url_for('dashboard'))
    if current_user.role == 'solicitante' and budget.solicitante_id != current_user.id:
        flash('Você só pode visualizar seus próprios orçamentos', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('view_budget.html', budget=budget)

@app.route('/budget/<int:id>/approve', methods=['POST'])
@login_required
def approve_budget(id):
    if current_user.role != 'aprovador':
        flash('Somente aprovadores podem aprovar orçamentos', 'danger')
        return redirect(url_for('dashboard'))
    
    budget = Budget.query.get_or_404(id)
    if budget.aprovador_id != current_user.id:
        flash('Você só pode aprovar orçamentos designados a você', 'danger')
        return redirect(url_for('dashboard'))
    
    justification = request.form['justification']
    budget.status = 'aprovado'
    budget.justification = justification
    db.session.commit()
    
    # Enviar email para o solicitante
    solicitante = User.query.get(budget.solicitante_id)
    send_notification_email(
        'Orçamento Aprovado',
        solicitante.email,
        f'Seu orçamento "{budget.title}" foi aprovado.\n\n'
        f'Aprovador: {current_user.name}\n'
        f'Justificativa: {justification}'
    )
    
    flash('Orçamento aprovado com sucesso', 'success')
    return redirect(url_for('dashboard'))

@app.route('/budget/<int:id>/reject', methods=['POST'])
@login_required
def reject_budget(id):
    if current_user.role != 'aprovador':
        flash('Somente aprovadores podem rejeitar orçamentos', 'danger')
        return redirect(url_for('dashboard'))
    
    budget = Budget.query.get_or_404(id)
    if budget.aprovador_id != current_user.id:
        flash('Você só pode rejeitar orçamentos designados a você', 'danger')
        return redirect(url_for('dashboard'))
    
    justification = request.form['justification']
    budget.status = 'rejeitado'
    budget.justification = justification
    db.session.commit()
    
    # Enviar email para o solicitante
    solicitante = User.query.get(budget.solicitante_id)
    send_notification_email(
        'Orçamento Rejeitado',
        solicitante.email,
        f'Seu orçamento "{budget.title}" foi rejeitado.\n\n'
        f'Aprovador: {current_user.name}\n'
        f'Justificativa: {justification}'
    )
    
    flash('Orçamento rejeitado com sucesso', 'success')
    return redirect(url_for('dashboard'))

@app.route('/download/<int:id>')
@login_required
def download_attachment(id):
    attachment = Attachment.query.get_or_404(id)
    budget = Budget.query.get(attachment.budget_id)
    
    if current_user.role == 'aprovador' and budget.aprovador_id != current_user.id:
        flash('Você não tem permissão para baixar este arquivo', 'danger')
        return redirect(url_for('dashboard'))
    if current_user.role == 'solicitante' and budget.solicitante_id != current_user.id:
        flash('Você não tem permissão para baixar este arquivo', 'danger')
        return redirect(url_for('dashboard'))
    
    return send_file(attachment.path, as_attachment=True)

@app.route('/agency/new', methods=['POST'])
@login_required
def new_agency():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Nome da agência é obrigatório'}), 400
    
    name = data['name'].strip()
    if not name:
        return jsonify({'error': 'Nome da agência não pode estar vazio'}), 400
    
    # Verifica se a agência já existe
    existing_agency = Agency.query.filter_by(name=name).first()
    if existing_agency:
        return jsonify({'error': 'Agência já existe'}), 400
    
    try:
        agency = Agency(
            name=name,
            created_by=current_user.id
        )
        db.session.add(agency)
        db.session.commit()
        return jsonify({'name': agency.name, 'id': agency.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar agência'}), 500

@app.route('/agencies', methods=['GET'])
@login_required
def get_agencies():
    agencies = Agency.query.order_by(Agency.name).all()
    return jsonify([{
        'id': a.id,
        'name': a.name
    } for a in agencies])

@app.route('/email-config', methods=['GET', 'POST'])
@login_required
def email_config():
    if current_user.role != 'administrador':
        flash('Apenas administradores podem acessar as configurações de email', 'danger')
        return redirect(url_for('dashboard'))
    
    config = EmailConfig.query.first()
    
    if request.method == 'POST':
        if not config:
            config = EmailConfig()
        
        config.smtp_server = request.form['smtp_server']
        config.smtp_port = int(request.form['smtp_port'])
        config.smtp_username = request.form['smtp_username']
        if request.form['smtp_password']:  # Só atualiza a senha se foi fornecida
            config.smtp_password = request.form['smtp_password']
        config.use_tls = 'use_tls' in request.form
        config.default_sender = request.form['default_sender']
        
        try:
            if not config.id:
                db.session.add(config)
            db.session.commit()
            config.update_mail_config()
            flash('Configurações de email atualizadas com sucesso', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar configurações: {str(e)}', 'danger')
    
    return render_template('email_config.html', config=config)

@app.route('/test-email')
@login_required
def test_email():
    if current_user.role != 'administrador':
        flash('Apenas administradores podem testar as configurações de email', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        send_notification_email(
            'Teste de Configuração de Email',
            current_user.email,
            'Este é um email de teste para verificar as configurações do servidor SMTP.'
        )
        flash('Email de teste enviado com sucesso! Verifique sua caixa de entrada.', 'success')
    except Exception as e:
        flash(f'Erro ao enviar email de teste: {str(e)}', 'danger')
    
    return redirect(url_for('email_config'))

@app.route('/user/<int:user_id>')
@login_required
def get_user(user_id):
    if current_user.role != 'administrador':
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'contact': user.contact,
        'role': user.role,
        'is_active': user.is_active
    })

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'administrador':
        flash('Acesso negado. Você não tem permissão para editar usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.contact = request.form['contact']
        user.role = request.form['role']
        
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'])
        
        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar usuário. Por favor, tente novamente.', 'danger')
            print(str(e))
    
    return render_template('edit_user.html', user=user)

@app.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'administrador':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Não permite desativar o próprio usuário
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Não é possível alterar seu próprio status'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/budget/<int:id>')
@login_required
def get_budget(id):
    if current_user.role != 'administrador':
        return jsonify({'error': 'Acesso não autorizado'}), 403
        
    budget = Budget.query.get_or_404(id)
    return jsonify({
        'id': budget.id,
        'solicitante': budget.solicitante.name,
        'description': budget.description,
        'status': budget.status,
        'observations': budget.observations,
        'aprovador': budget.aprovador.name if budget.aprovador else None,
        'approved_at': budget.approved_at.strftime('%d/%m/%Y %H:%M') if budget.approved_at else None
    })

@app.route('/budget/<int:id>/edit', methods=['POST'])
@login_required
def edit_budget(id):
    if current_user.role != 'administrador':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
        
    budget = Budget.query.get_or_404(id)
    data = request.get_json()
    
    try:
        budget.status = data['status']
        budget.observations = data['observations']
        if data['status'] == 'aprovado' and budget.status != 'aprovado':
            budget.approved_at = datetime.utcnow()
            budget.aprovador_id = current_user.id
        db.session.commit()
        
        # Enviar email de notificação
        subject = f'Atualização da Solicitação #{budget.id}'
        recipient = budget.solicitante.email
        body = f'''Sua solicitação #{budget.id} foi atualizada.
        Status: {budget.status}
        Observações: {budget.observations or 'Nenhuma'}
        '''
        send_notification_email(subject, recipient, body)
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/budget/<int:id>/inactivate', methods=['POST'])
@login_required
def inactivate_budget(id):
    if current_user.role != 'administrador':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
        
    budget = Budget.query.get_or_404(id)
    
    try:
        budget.status = 'rejeitado'
        budget.observations = 'Inativado pelo administrador'
        db.session.commit()
        
        # Enviar email de notificação
        subject = f'Solicitação #{budget.id} Inativada'
        recipient = budget.solicitante.email
        body = f'''Sua solicitação #{budget.id} foi inativada por um administrador.
        Por favor, entre em contato se precisar de mais informações.
        '''
        send_notification_email(subject, recipient, body)
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Aqui você pode implementar o envio de email com o token
            # Por enquanto, vamos apenas redirecionar
            flash('Verifique seu email para instruções de redefinição de senha', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email não encontrado', 'danger')
    
    return render_template('reset_password_request.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Aqui você implementaria a verificação do token
    # Por enquanto, vamos apenas mostrar o formulário
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Implementar a alteração da senha
        flash('Sua senha foi alterada com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'administrador':
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all users
    users = User.query.all()
    
    # Get user statistics
    total_users = len(users)
    solicitantes = sum(1 for u in users if u.role == 'solicitante')
    aprovadores = sum(1 for u in users if u.role == 'aprovador')
    administradores = sum(1 for u in users if u.role == 'administrador')
    
    # Get all budgets
    budgets = Budget.query.all()
    
    # Get budget statistics for the current user
    user_pendente = sum(1 for b in budgets if b.solicitante_id == current_user.id and b.status == 'pendente')
    user_aprovado = sum(1 for b in budgets if b.solicitante_id == current_user.id and b.status == 'aprovado')
    user_rejeitado = sum(1 for b in budgets if b.solicitante_id == current_user.id and b.status == 'rejeitado')
    
    return render_template('admin_dashboard.html',
                         budgets=budgets,
                         users=users,
                         total_users=total_users,
                         solicitantes=solicitantes,
                         aprovadores=aprovadores,
                         administradores=administradores,
                         user_pendente=user_pendente,
                         user_aprovado=user_aprovado,
                         user_rejeitado=user_rejeitado)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Atualizar informações do usuário
            current_user.name = request.form.get('name')
            current_user.contact = request.form.get('contact')
            
            # Se uma nova senha foi fornecida, atualiza
            new_password = request.form.get('new_password')
            if new_password:
                current_user.set_password(new_password)
            
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')
    
    return render_template('profile.html', user=current_user)
