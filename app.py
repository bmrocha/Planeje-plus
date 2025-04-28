import os
from flask import Flask, redirect, url_for, render_template
from flask_login import current_user, LoginManager
from config import Config
from extensions import db, login_manager, migrate, csrf
from functools import wraps
from flask import abort
from models import User
from routes import auth, budget, admin

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    with app.app_context():
        # Register blueprints
        app.register_blueprint(auth.bp)
        app.register_blueprint(budget.bp, url_prefix='/budget')
        app.register_blueprint(admin.bp, url_prefix='/admin')

        # Register root route
        @app.route('/')
        def index():
            if current_user.is_authenticated:
                if current_user.role == 'administrador':
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('budget.dashboard'))
            return redirect(url_for('auth.login'))

        # Error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            return render_template('errors/500.html'), 500

        # Template globals
        app.jinja_env.globals.update(
            is_admin=lambda: current_user.is_authenticated and current_user.role == 'admin',
            is_approver=lambda: current_user.is_authenticated and current_user.role == 'approver',
            is_requester=lambda: current_user.is_authenticated and current_user.role == 'requester'
        )

        return app

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
