from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    contato = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    # relação 1:N -> um usuário pode ter vários animais (como tutor)
    animais = db.relationship('Animal', backref='dono', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    endereco = db.Column(db.String(255), nullable=True)
    telefone = db.Column(db.String(100), nullable=True)

    # usuário responsável (conta de clínica)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('clinic', uselist=False))

    # relação com animais atendidos
    animais = db.relationship('Animal', backref='clinic', lazy=True)


class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    especie = db.Column(db.String(100), nullable=False)
    raca = db.Column(db.String(100), nullable=True)
    idade = db.Column(db.Integer, nullable=True)
    contato = db.Column(db.String(100), nullable=True)
    procedimento = db.Column(db.String(200), nullable=True)

    dono_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)

    data_agendamento = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Aguardando')
    verification_token = db.Column(db.String(64), nullable=True)
    token_validated = db.Column(db.Boolean, nullable=False, default=False)
    data_conclusao = db.Column(db.DateTime, nullable=True)

    @property
    def agendamento(self):
        return self.data_agendamento.strftime('%d/%m/%Y %H:%M') if self.data_agendamento else ''
