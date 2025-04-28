from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import User, Sector, db
from werkzeug.security import generate_password_hash
from functools import wraps
from forms import EditUserForm

bp = Blueprint('admin', __name__)

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Você não tem permissão para acessar esta página.', 'error')
                return redirect(url_for('budget.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/dashboard')
@login_required
@role_required('administrador')
def admin_dashboard():
    if current_user.role != 'administrador':
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('budget.dashboard'))

    # Contagem de usuários por tipo
    total_compras = User.query.filter_by(role='compras').count()
    total_solicitantes = User.query.filter_by(role='solicitante').count()
    total_aprovadores = User.query.filter_by(role='aprovador').count()
    total_administradores = User.query.filter_by(role='administrador').count()

    # Buscar todos os usuários
    users = User.query.all()

    return render_template('admin_dashboard.html',
                         users=users,
                         total_compras=total_compras,
                         total_solicitantes=total_solicitantes,
                         total_aprovadores=total_aprovadores,
                         total_administradores=total_administradores)

@bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.role = form.role.data
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        
        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    return render_template('edit_user.html', form=form, user=user)

@bp.route('/toggle_user/<int:user_id>')
@login_required
@role_required('administrador')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'ativado' if user.is_active else 'desativado'
    flash(f'Usuário {status} com sucesso!', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@bp.route('/create_sector', methods=['POST'])
@login_required
@role_required('administrador')
def create_sector():
    try:
        name = request.form.get('name')
        if not name:
            return jsonify({'success': False, 'message': 'Nome do setor é obrigatório'}), 400
        
        # Verificar se o setor já existe
        existing_sector = Sector.query.filter_by(name=name).first()
        if existing_sector:
            return jsonify({'success': False, 'message': 'Este setor já existe'}), 400
        
        # Criar novo setor
        sector = Sector(name=name)
        db.session.add(sector)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Setor criado com sucesso',
            'sector': {
                'id': sector.id,
                'name': sector.name
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/get_sectors')
@login_required
def get_sectors():
    sectors = Sector.query.all()
    return jsonify([{'id': s.id, 'name': s.name} for s in sectors])
