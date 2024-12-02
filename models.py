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
    role = db.Column(db.String(20), nullable=False)  # 'administrador', 'aprovador', 'solicitante'
    is_active = db.Column(db.Boolean, default=True)
    budgets_requested = db.relationship('Budget', backref='solicitante', lazy=True, foreign_keys='Budget.solicitante_id')
    budgets_approved = db.relationship('Budget', backref='aprovador', lazy=True, foreign_keys='Budget.aprovador_id')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requested_name = db.Column(db.String(100), nullable=False)  # Nome do Cadastrador
    solicitado = db.Column(db.String(100), nullable=False)  # Nome do Solicitante
    sector = db.Column(db.String(100), nullable=False)  # Setor (antigo agency)
    status = db.Column(db.String(20), default='pendente')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    aprovador_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    companies = db.relationship('Company', backref='budget', lazy=True, cascade='all, delete-orphan')

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    attachment_filename = db.Column(db.String(200))
    attachment_path = db.Column(db.String(500))

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(100), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=False)
    smtp_username = db.Column(db.String(100), nullable=False)
    smtp_password = db.Column(db.String(100), nullable=False)
    use_tls = db.Column(db.Boolean, default=True)
    default_sender = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
