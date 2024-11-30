import os
import secrets

class Config:
    # Gera uma chave secreta fixa para desenvolvimento
    dev_key = '2d9c6d66890c4a2b948f54c42e05b0c8'
    SECRET_KEY = os.environ.get('SECRET_KEY', dev_key)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}
