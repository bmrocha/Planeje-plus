import os
from app import db, User, app, Budget, Agency, EmailConfig
from werkzeug.security import generate_password_hash
from datetime import datetime

# Remove o banco de dados existente
db_path = os.path.join('instance', 'budget.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Banco de dados antigo removido: {db_path}")

# Cria o diretório instance se não existir
if not os.path.exists('instance'):
    os.makedirs('instance')
    print("Diretório instance criado")

# Cria as tabelas do banco de dados
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Novas tabelas criadas")

    # Cria o usuário admin padrão
    admin = User(
        name='Administrador',
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        role='administrador',
        is_active=True
    )
    db.session.add(admin)
    
    # Configuração de email padrão
    email_config = EmailConfig(
        smtp_server='smtp.gmail.com',
        smtp_port=587,
        smtp_username='seu-email@gmail.com',
        smtp_password='sua-senha-de-app',
        use_tls=True,
        default_sender='Sistema de Orçamentos'
    )
    db.session.add(email_config)

    db.session.commit()
    print("Usuário administrador criado")
    print("Banco de dados recriado com sucesso!")
