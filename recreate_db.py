import os
from app import db, User, app, Budget, Sector
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
    
    # Adicionar setores iniciais
    setores = ['TI', 'RH', 'Financeiro', 'Comercial', 'Marketing', 'Operações']
    for setor in setores:
        sector = Sector(name=setor)
        db.session.add(sector)
    
    # Commit das alterações
    db.session.commit()
    print("Usuário administrador criado")
    print("Banco de dados recriado com sucesso!")
