from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from email_validator import validate_email, EmailNotValidError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    contact = StringField('Contato')
    role = SelectField('Função', choices=[
        ('solicitante', 'Solicitante'),
        ('aprovador', 'Aprovador'),
        ('administrador', 'Administrador'),
        ('compras', 'Compras')
    ], validators=[DataRequired()])
    submit = SubmitField('Registrar')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[DataRequired()])
    password2 = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Redefinir Senha')

class BudgetForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Descrição', validators=[DataRequired(), Length(min=10)])
    solicitado = StringField('Solicitante', validators=[DataRequired()])
    sector = SelectField('Setor', validators=[DataRequired()])
    aprovador_id = SelectField('Aprovador', validators=[DataRequired()])
    compras_id = SelectField('Compras', validators=[DataRequired()])

class EditUserForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Nova Senha', validators=[Optional()])
    contact = StringField('Contato')
    role = SelectField('Função', choices=[
        ('solicitante', 'Solicitante'),
        ('aprovador', 'Aprovador'),
        ('administrador', 'Administrador'),
        ('compras', 'Compras')
    ], validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')
