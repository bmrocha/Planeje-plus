from flask import Flask
from config import Config
from extensions import db, login_manager, mail, migrate, csrf
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance and uploads directories exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    return app

app = create_app()

# Import routes after app is created
from routes import *

if __name__ == '__main__':
    with app.app_context():
        from models import User, Budget, Company, Sector, EmailConfig
        db.create_all()
    app.run(debug=True)
