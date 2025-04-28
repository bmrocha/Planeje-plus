from app import create_app
from models import db, User, Budget, Company, Sector
import json
from datetime import datetime

app = create_app()

with app.app_context():
    # Criar usuário admin e compras primeiro
    admin = User(
        name='Administrador',
        email='admin@example.com',
        role='administrador',
        is_active=True
    )
    admin.set_password('admin123')
    
    compras = User(
        name='Compras',
        email='compras@example.com',
        role='compras',
        is_active=True
    )
    compras.set_password('compras123')
    
    db.session.add(admin)
    db.session.add(compras)
    db.session.commit()
    
    try:
        # Carregar dados do backup
        with open('backup_data.json', 'r') as f:
            data = json.load(f)
        
        # Restaurar setores
        for sector_data in data['sectors']:
            sector = Sector(
                name=sector_data['name'],
                created_at=datetime.fromisoformat(sector_data['created_at']) if sector_data['created_at'] else None
            )
            db.session.add(sector)
        
        # Restaurar usuários (exceto admin e compras que já foram criados)
        for user_data in data['users']:
            if user_data['email'] not in ['admin@example.com', 'compras@example.com']:
                user = User(
                    name=user_data['name'],
                    email=user_data['email'],
                    role=user_data['role'],
                    is_active=user_data['is_active'],
                    contact=user_data['contact']
                )
                user.set_password('senha123')  # senha padrão para usuários restaurados
                db.session.add(user)
        
        db.session.commit()
        print("Dados restaurados com sucesso!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao restaurar dados: {str(e)}") 