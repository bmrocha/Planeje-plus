from app import create_app
from models import db, Budget, User

app = create_app()

with app.app_context():
    # Encontra um usuário de compras
    compras_user = User.query.filter_by(role='compras').first()
    
    if not compras_user:
        # Cria um usuário de compras se não existir
        compras_user = User(
            name='Compras',
            email='compras@example.com',
            role='compras',
            is_active=True
        )
        compras_user.set_password('senha123')
        db.session.add(compras_user)
        db.session.commit()
    
    # Atualiza todos os orçamentos existentes
    budgets = Budget.query.all()
    for budget in budgets:
        budget.compras_id = compras_user.id
    
    db.session.commit() 