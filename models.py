from flask_login import UserMixin
from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)  # 'administrador', 'aprovador', 'solicitante', 'compras'
    is_active = db.Column(db.Boolean, default=True)

    # Relacionamentos com orçamentos
    budgets_requested = db.relationship('Budget', 
                                      foreign_keys='Budget.solicitante_id',
                                      backref=db.backref('requester', lazy=True))
    
    budgets_to_approve = db.relationship('Budget', 
                                       foreign_keys='Budget.aprovador_id',
                                       backref=db.backref('assigned_approver', lazy=True))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.name}>'

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    solicitado = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pendente')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    solicitante_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    aprovador_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    compras_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Campos de aprovação/rejeição
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    approval_reason = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # Relacionamentos
    companies = db.relationship('Company', 
                              foreign_keys='Company.budget_id',
                              backref=db.backref('budget', lazy=True), 
                              lazy=True, 
                              cascade='all, delete-orphan')
    compras_user = db.relationship('User',
                                 foreign_keys=[compras_id],
                                 backref=db.backref('budgets_to_process', lazy=True))

    @property
    def creator(self):
        return self.requester

    def __repr__(self):
        return f'<Budget {self.title}>'

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')  # pendente, aprovado, rejeitado
    attachment_filename = db.Column(db.String(255))
    attachment_path = db.Column(db.String(255))
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id', name='fk_company_budget'), nullable=False)

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
