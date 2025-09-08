from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db  # Utiliza a instância única configurada em extensions.py

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    phone_whatsapp = db.Column(db.String(15), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Integer, default=0)

    filhos = db.relationship('Filho', backref='user', lazy=True)
    # Relação bidirecional com Appointment usando back_populates
    appointments = db.relationship('Appointment', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.email}>"

class Filho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    nome_pai = db.Column(db.String(100), nullable=False)
    nome_mae = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Filho {self.nome_completo}>"

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    crm = db.Column(db.String(20), unique=True, nullable=False)
    specialty = db.Column(db.String(50), nullable=False)
    appointments = db.relationship('Appointment', back_populates='doctor', lazy=True)
    avaliacoes = db.relationship('Avaliacao', back_populates='doctor', lazy=True)

    def __repr__(self):
        return f"<Doctor {self.name}>"

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    appointment_date = db.Column(db.DateTime)  # Data da consulta
    scheduling_date = db.Column(db.DateTime, default=datetime.utcnow)  # Data do agendamento
    status = db.Column(db.String(50))
    new_appointment_date = db.Column(db.DateTime, nullable=True)
    # Campos para compatibilidade com formulários e consultas da aplicação:
    appointment_type = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    # Campo adicional; se não for utilizado, pode ser removido:
    reason = db.Column(db.String(100), nullable=True)

    # Relação bidirecional com User usando back_populates
    user = db.relationship('User', back_populates='appointments')
    # Relação com Doctor
    doctor = db.relationship('Doctor', back_populates='appointments')

    @property
    def waiting_time(self):
        """Calcula o tempo de espera em dias (agendamento -> data da consulta)"""
        if self.appointment_date and self.scheduling_date:
            return (self.appointment_date - self.scheduling_date).days
        return None

    def __repr__(self):
        return f"<Appointment {self.id}>"

class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    satisfaction_score = db.Column(db.Integer, nullable=False)  # Nota de 1 a 5
    comentarios = db.Column(db.Text, nullable=True)
    data_avaliacao = db.Column(db.DateTime, default=db.func.current_timestamp())

    doctor = db.relationship('Doctor', back_populates='avaliacoes')

    def __repr__(self):
        return f"<Avaliacao {self.id} - Doctor {self.doctor_id}>"
