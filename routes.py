from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'administrador':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('budget.dashboard'))
    return redirect(url_for('auth.login'))
