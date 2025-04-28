from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Budget, Company, Sector, User, db
from forms import BudgetForm
from datetime import datetime
import os

bp = Blueprint('budget', __name__)

@bp.route('/dashboard')
@bp.route('/dashboard/<status>')
@login_required
def dashboard(status='pendente'):
    if current_user.role == 'solicitante':
        if status == 'todos':
            budgets = Budget.query.filter_by(solicitante_id=current_user.id).order_by(Budget.request_date.desc()).all()
        else:
            budgets = Budget.query.filter_by(solicitante_id=current_user.id, status=status).order_by(Budget.request_date.desc()).all()
        
        total_pendente = Budget.query.filter_by(solicitante_id=current_user.id, status='pendente').count()
        total_aprovado = Budget.query.filter_by(solicitante_id=current_user.id, status='aprovado').count()
        total_rejeitado = Budget.query.filter_by(solicitante_id=current_user.id, status='rejeitado').count()
        
        return render_template('dashboard.html', 
                             budgets=budgets,
                             user_pendente=total_pendente,
                             user_aprovado=total_aprovado,
                             user_rejeitado=total_rejeitado,
                             current_status=status)
    
    elif current_user.role == 'compras':
        # Buscar orçamentos aprovados para o Kanban
        approved_budgets = Budget.query.filter_by(status='aprovado').order_by(Budget.request_date.desc()).all()
        processing_budgets = Budget.query.filter_by(status='processing').order_by(Budget.request_date.desc()).all()
        completed_budgets = Budget.query.filter_by(status='completed').order_by(Budget.request_date.desc()).all()
        
        return render_template('compras_dashboard.html',
                             approved_budgets=approved_budgets,
                             approved_count=len(approved_budgets),
                             processing_budgets=processing_budgets,
                             processing_count=len(processing_budgets),
                             completed_budgets=completed_budgets,
                             completed_count=len(completed_budgets))
    
    elif current_user.role == 'aprovador':
        if status == 'todos':
            budgets = Budget.query.filter_by(aprovador_id=current_user.id).order_by(Budget.request_date.desc()).all()
        else:
            budgets = Budget.query.filter_by(aprovador_id=current_user.id, status=status).order_by(Budget.request_date.desc()).all()
        
        total_pendente = Budget.query.filter_by(aprovador_id=current_user.id, status='pendente').count()
        total_aprovado = Budget.query.filter_by(aprovador_id=current_user.id, status='aprovado').count()
        total_rejeitado = Budget.query.filter_by(aprovador_id=current_user.id, status='rejeitado').count()
        
        return render_template('dashboard.html', 
                             budgets=budgets,
                             user_pendente=total_pendente,
                             user_aprovado=total_aprovado,
                             user_rejeitado=total_rejeitado,
                             current_status=status)
    
    elif current_user.role == 'administrador':
        return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('dashboard.html', budgets=[])

@bp.route('/create_budget', methods=['GET', 'POST'])
@login_required
def create_budget():
    if current_user.role == 'administrador':
        flash('Administradores não podem criar orçamentos.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    form = BudgetForm()
    sectors = Sector.query.order_by(Sector.name).all()
    aprovadores = User.query.filter_by(role='aprovador', is_active=True).order_by(User.name).all()
    compras_users = User.query.filter_by(role='compras', is_active=True).order_by(User.name).all()
    
    form.sector.choices = [(s.name, s.name) for s in sectors]
    form.aprovador_id.choices = [(str(u.id), u.name) for u in aprovadores]
    form.compras_id.choices = [(str(u.id), u.name) for u in compras_users]
    
    if form.validate_on_submit():
        try:
            budget = Budget(
                title=form.title.data,
                description=form.description.data,
                solicitado=form.solicitado.data,
                sector=form.sector.data,
                solicitante_id=current_user.id,
                aprovador_id=int(form.aprovador_id.data),
                compras_id=int(form.compras_id.data),
                status='pendente',
                request_date=datetime.utcnow()
            )
            db.session.add(budget)
            
            # Processar empresas
            company_names = request.form.getlist('company_name[]')
            company_values = request.form.getlist('company_value[]')
            company_files = request.files.getlist('company_attachment[]')
            
            for name, value, file in zip(company_names, company_values, company_files):
                if name and value:  # Se nome e valor foram fornecidos
                    # Criar nova empresa
                    company = Company(
                        name=name,
                        value=float(value.replace('R$', '').replace('.', '').replace(',', '.').strip()),
                        budget=budget
                    )
                    
                    # Processar anexo se fornecido
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(filepath)
                        company.attachment_path = filepath
                        company.attachment_filename = filename
                    
                    db.session.add(company)
            
            db.session.commit()
            flash('Orçamento criado com sucesso!', 'success')
            return redirect(url_for('budget.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar orçamento: {str(e)}', 'error')
            return redirect(url_for('budget.create_budget'))
    
    return render_template('create_budget.html', form=form, sectors=sectors, aprovadores=aprovadores, compras_users=compras_users)

@bp.route('/view_budget/<int:id>')
@login_required
def view_budget(id):
    budget = Budget.query.get_or_404(id)
    return render_template('view_budget.html', budget=budget)

@bp.route('/approve/<int:budget_id>', methods=['POST'])
@login_required
def approve_budget(budget_id):
    # Verifica se é uma requisição AJAX
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'message': 'Requisição inválida'}), 400
        
    if current_user.role != 'aprovador':
        return jsonify({'success': False, 'message': 'Você não tem permissão para aprovar orçamentos.'}), 403
    
    try:
        data = request.get_json()
        print(f"Dados recebidos: {data}")  # Debug
        
        if not data:
            return jsonify({'success': False, 'message': 'Dados não recebidos'}), 400
        
        reason = data.get('reason', '').strip()
        selected_company_id = data.get('selected_company_id')
        
        if not reason:
            return jsonify({'success': False, 'message': 'A justificativa é obrigatória.'}), 400
        
        if not selected_company_id:
            return jsonify({'success': False, 'message': 'Selecione uma empresa para aprovar.'}), 400
        
        budget = Budget.query.get_or_404(budget_id)
        
        if budget.status != 'pendente':
            return jsonify({'success': False, 'message': 'Este orçamento não está mais pendente.'}), 400
        
        if budget.aprovador_id != current_user.id:
            return jsonify({'success': False, 'message': 'Você não é o aprovador designado para este orçamento.'}), 403
        
        # Atualiza o orçamento
        budget.status = 'aprovado'
        budget.approved_at = datetime.utcnow()
        budget.approval_reason = reason
        
        # Atualiza o status das empresas
        for company in budget.companies:
            if str(company.id) == str(selected_company_id):
                company.status = 'aprovado'
            else:
                company.status = 'rejeitado'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Orçamento aprovado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao aprovar orçamento: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/reject/<int:budget_id>', methods=['POST'])
@login_required
def reject_budget(budget_id):
    if current_user.role != 'aprovador':
        return jsonify({'success': False, 'message': 'Você não tem permissão para rejeitar orçamentos.'})
    
    data = request.get_json()
    reason = data.get('reason')
    
    if not reason:
        return jsonify({'success': False, 'message': 'O motivo da rejeição é obrigatório.'})
    
    budget = Budget.query.get_or_404(budget_id)
    if budget.aprovador_id != current_user.id:
        return jsonify({'success': False, 'message': 'Você não é o aprovador designado para este orçamento.'})
    
    try:
        budget.status = 'rejeitado'
        budget.rejected_at = datetime.utcnow()
        budget.rejection_reason = reason
        
        # Atualizar status de todas as empresas para rejeitado
        for company in budget.companies:
            company.status = 'rejeitado'
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Orçamento rejeitado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/download_attachment/<int:company_id>')
@login_required
def download_attachment(company_id):
    company = Company.query.get_or_404(company_id)
    
    if not company.attachment_path or not os.path.exists(company.attachment_path):
        flash('Arquivo não encontrado.', 'error')
        return redirect(url_for('budget.view_budget', id=company.budget_id))
    
    return send_file(company.attachment_path,
                    download_name=company.attachment_filename,
                    as_attachment=True)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_budget(id):
    budget = Budget.query.get_or_404(id)
    
    # Verifica se o orçamento pode ser editado
    if budget.status != 'pendente':
        flash(f'Este orçamento não pode ser editado pois está {budget.status}.', 'error')
        return redirect(url_for('budget.dashboard'))
    
    if current_user.role != 'solicitante' or budget.solicitante_id != current_user.id:
        flash('Você não tem permissão para editar este orçamento.', 'error')
        return redirect(url_for('budget.dashboard'))
    
    form = BudgetForm(obj=budget)
    sectors = Sector.query.order_by(Sector.name).all()
    aprovadores = User.query.filter_by(role='aprovador', is_active=True).order_by(User.name).all()
    
    form.sector.choices = [(s.name, s.name) for s in Sector.query.order_by(Sector.name)]
    form.aprovador_id.choices = [(str(u.id), u.name) for u in User.query.filter_by(role='aprovador')]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(budget)
            
            # Processar empresas
            company_names = request.form.getlist('companies[][name]')
            company_values = request.form.getlist('companies[][value]')
            company_ids = request.form.getlist('companies[][id]')
            company_files = request.files.getlist('companies[][attachment]')
            
            # Remover empresas que não estão mais no formulário
            for company in budget.companies[:]:
                if str(company.id) not in company_ids:
                    if company.attachment_path and os.path.exists(company.attachment_path):
                        os.remove(company.attachment_path)
                    db.session.delete(company)
            
            # Atualizar ou criar empresas
            for i, (name, value) in enumerate(zip(company_names, company_values)):
                if name.strip():
                    try:
                        value_float = float(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
                        
                        if i < len(company_ids) and company_ids[i]:
                            # Atualizar empresa existente
                            company = Company.query.get(company_ids[i])
                            if company:
                                company.name = name
                                company.value = value_float
                                
                                # Processar novo anexo se fornecido
                                if company_files[i] and company_files[i].filename:
                                    if company.attachment_path and os.path.exists(company.attachment_path):
                                        os.remove(company.attachment_path)
                                    filename = secure_filename(company_files[i].filename)
                                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                                    company_files[i].save(filepath)
                                    company.attachment_path = filepath
                                    company.attachment_filename = filename
                        else:
                            # Criar nova empresa
                            company = Company(
                                name=name,
                                value=value_float,
                                budget_id=budget.id
                            )
                            
                            if company_files[i] and company_files[i].filename:
                                filename = secure_filename(company_files[i].filename)
                                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                                company_files[i].save(filepath)
                                company.attachment_path = filepath
                                company.attachment_filename = filename
                            
                            db.session.add(company)
                    except ValueError as e:
                        flash(f'Valor inválido para a empresa {name}: {str(e)}', 'error')
                        return redirect(url_for('budget.edit_budget', id=id))
            
            db.session.commit()
            flash('Orçamento atualizado com sucesso!', 'success')
            return redirect(url_for('budget.view_budget', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar orçamento: {str(e)}', 'error')
    
    return render_template('edit_budget.html', 
                         form=form, 
                         budget=budget,
                         sectors=sectors,
                         aprovadores=aprovadores)

@bp.route('/create_sector', methods=['POST'])
@login_required
def create_sector():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'success': False, 'message': 'Nome do setor é obrigatório'}), 400
        
        sector_name = data['name'].strip()
        if not sector_name:
            return jsonify({'success': False, 'message': 'Nome do setor não pode estar vazio'}), 400
            
        # Verifica se o setor já existe
        existing_sector = Sector.query.filter_by(name=sector_name).first()
        if existing_sector:
            return jsonify({'success': False, 'message': 'Este setor já existe'}), 400
            
        # Cria novo setor
        new_sector = Sector(name=sector_name)
        db.session.add(new_sector)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Setor criado com sucesso',
            'sector': {'id': new_sector.id, 'name': new_sector.name}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/<int:budget_id>/update_status', methods=['POST'])
@login_required
def update_budget_status(budget_id):
    if current_user.role != 'compras':
        return jsonify({'success': False, 'message': 'Permissão negada'}), 403
        
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status não fornecido'}), 400
            
        budget = Budget.query.get_or_404(budget_id)
        budget.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status atualizado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
