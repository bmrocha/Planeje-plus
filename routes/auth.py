from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
from forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_wtf.csrf import CSRFProtect

bp = Blueprint('auth', __name__)
csrf = CSRFProtect()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('budget.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('budget.dashboard'))
        flash('Email ou senha inválidos.', 'error')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'administrador':
        flash('Acesso negado. Você não tem permissão para registrar usuários.', 'error')
        return redirect(url_for('budget.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verificar se o email já existe
        if User.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data,
            password=generate_password_hash(form.password.data),
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('register.html', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('budget.dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Aqui você implementaria o envio do email
            # Por enquanto, apenas redirecionamos
            flash('Instruções para redefinir sua senha foram enviadas para seu email.', 'info')
            return redirect(url_for('auth.login'))
        flash('Email não encontrado.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    
    return render_template('reset_password_request.html', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('budget.dashboard'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Aqui você implementaria a validação do token e a alteração da senha
        flash('Sua senha foi alterada com sucesso.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form)
