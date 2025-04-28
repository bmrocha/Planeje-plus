from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    # Criar usuário administrador
    admin = User(
        name='Administrador',
        email='admin@example.com',
        role='administrador',
        is_active=True
    )
    admin.set_password('admin123')
    
    # Criar usuário de compras padrão
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