from app import create_app
from models import db, User, Budget, Company, Sector
import json
from datetime import datetime

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

app = create_app()

with app.app_context():
    # Backup Users
    users = User.query.all()
    users_data = [{
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'is_active': u.is_active,
        'contact': u.contact
    } for u in users]
    
    # Backup Sectors
    sectors = Sector.query.all()
    sectors_data = [{
        'name': s.name,
        'created_at': s.created_at
    } for s in sectors]
    
    # Backup Budgets and Companies
    budgets = Budget.query.all()
    budgets_data = []
    for b in budgets:
        companies = [{
            'name': c.name,
            'value': c.value,
            'status': c.status
        } for c in b.companies]
        
        budgets_data.append({
            'title': b.title,
            'description': b.description,
            'solicitado': b.solicitado,
            'sector': b.sector,
            'status': b.status,
            'request_date': b.request_date,
            'companies': companies
        })

    # Save to file
    with open('backup_data.json', 'w') as f:
        json.dump({
            'users': users_data,
            'sectors': sectors_data,
            'budgets': budgets_data
        }, f, default=serialize_datetime, indent=2) 