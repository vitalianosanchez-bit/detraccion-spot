from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Empresa(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(100), nullable=False)
    ruc      = db.Column(db.String(11), unique=True, nullable=False)
    cuenta   = db.Column(db.String(20))
    activa   = db.Column(db.Boolean, default=True)
    creada   = db.Column(db.DateTime, default=datetime.utcnow)
    usuarios    = db.relationship('Usuario', backref='empresa', lazy=True)
    proveedores = db.relationship('Proveedor', backref='empresa', lazy=True)
    clientes    = db.relationship('Cliente',   backref='empresa', lazy=True)

class Usuario(db.Model, UserMixin):
    id         = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nombre     = db.Column(db.String(100), nullable=False)
    username   = db.Column(db.String(50), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    rol        = db.Column(db.String(20), default='usuario')  # superadmin | admin | usuario
    activo     = db.Column(db.Boolean, default=True)

    def set_password(self, pw):
        self.password = generate_password_hash(pw)
    def check_password(self, pw):
        return check_password_hash(self.password, pw)

class Proveedor(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    ruc        = db.Column(db.String(15), nullable=False)
    razon      = db.Column(db.String(200), nullable=False)
    cuenta     = db.Column(db.String(20))
    direccion  = db.Column(db.String(200))
    cod_bs     = db.Column(db.String(5))
    pct        = db.Column(db.Float, default=0)
    afecto_auto= db.Column(db.Boolean, default=False)

class Cliente(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    ruc        = db.Column(db.String(15), nullable=False)
    razon      = db.Column(db.String(200), nullable=False)
    cuenta     = db.Column(db.String(20))
    direccion  = db.Column(db.String(200))

class TipoOperacion(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    cod        = db.Column(db.String(5), nullable=False)
    descripcion= db.Column(db.String(200), nullable=False)
    validado   = db.Column(db.Boolean, default=True)

class BienServicio(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    cod        = db.Column(db.String(5), nullable=False)
    descripcion= db.Column(db.String(200), nullable=False)
    pct        = db.Column(db.Float, nullable=False)
    anexo      = db.Column(db.Integer, nullable=False)
    validado   = db.Column(db.Boolean, default=True)
