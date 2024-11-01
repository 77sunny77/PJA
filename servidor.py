import os
from datetime import datetime
from typing import Optional, List

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__, template_folder='templates')

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'loja.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelos Base
class ModeloBase:
    def criar(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def deletar(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

# Modelos
class Cliente(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    login = db.Column(db.String(20), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)  # Aumentado para hash
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    vendas = db.relationship('Venda', backref='cliente', lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def ler(codigo: int) -> Optional['Cliente']:
        return Cliente.query.get(codigo)

    @staticmethod
    def ler_todos() -> List['Cliente']:
        return Cliente.query.all()

    def atualizar(self, nome: str = None, login: str = None, senha: str = None, cpf: str = None):
        try:
            if nome: self.nome = nome
            if login: self.login = login
            if senha: self.senha = senha  # Aqui deveria ter hash
            if cpf: self.cpf = cpf
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class FormaPagamento(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    bandeira_cartao = db.Column(db.String(20))
    numero_parcelas = db.Column(db.Integer, default=1)
    numero_cartao = db.Column(db.String(16))
    codigo_boleto = db.Column(db.String(50))
    chave_pix = db.Column(db.String(50))
    vendas = db.relationship('Venda', backref='forma_pagamento', lazy=True)

    @staticmethod
    def ler(codigo: int) -> Optional['FormaPagamento']:
        return FormaPagamento.query.get(codigo)

    @staticmethod
    def ler_todos() -> List['FormaPagamento']:
        return FormaPagamento.query.all()

    def atualizar(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class FormaEntrega(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    data_agendada = db.Column(db.Date)
    valor_frete = db.Column(db.Float, nullable=False)
    vendas = db.relationship('Venda', backref='forma_entrega', lazy=True)

    @staticmethod
    def ler(codigo: int) -> Optional['FormaEntrega']:
        return FormaEntrega.query.get(codigo)

    @staticmethod
    def ler_todos() -> List['FormaEntrega']:
        return FormaEntrega.query.all()

    def atualizar(self, tipo: str = None, data_agendada: datetime = None, valor_frete: float = None):
        try:
            if tipo: self.tipo = tipo
            if data_agendada: self.data_agendada = data_agendada
            if valor_frete: self.valor_frete = valor_frete
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class Venda(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    cod_cli = db.Column(db.Integer, db.ForeignKey('cliente.codigo'), nullable=False)
    cod_formapagamento = db.Column(db.Integer, db.ForeignKey('forma_pagamento.codigo'), nullable=False)
    cod_formaentrega = db.Column(db.Integer, db.ForeignKey('forma_entrega.codigo'), nullable=False)
    rua = db.Column(db.String(100), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(50))
    bairro = db.Column(db.String(50), nullable=False)
    cidade = db.Column(db.String(50), nullable=False)
    cep = db.Column(db.String(9), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    itens = db.relationship('Item', backref='venda', lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def ler(codigo: int) -> Optional['Venda']:
        return Venda.query.get(codigo)

    @staticmethod
    def ler_todos() -> List['Venda']:
        return Venda.query.all()

    def atualizar(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class Departamento(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    produtos = db.relationship('Produto', backref='departamento', lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def ler(codigo: int) -> Optional['Departamento']:
        return Departamento.query.get(codigo)

    @staticmethod
    def ler_todos() -> List['Departamento']:
        return Departamento.query.all()

    def atualizar(self, nome: str = None):
        try:
            if nome: self.nome = nome
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class Produto(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200))
    preco_compra = db.Column(db.Float, nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)
    qtd_estoque = db.Column(db.Integer, nullable=False, default=0)
    uni_compra = db.Column(db.Integer, nullable=False)
    uni_venda = db.Column(db.Integer, nullable=False)
    cod_departamento = db.Column(db.Integer, db.ForeignKey('departamento.codigo'), nullable=False)
    itens = db.relationship('Item', backref='produto', lazy=True)

    @staticmethod
    def ler(codigo: int) -> Optional['Produto']:
        return Produto.query.get(codigo)

    @staticmethod
    def ler_todos() -> List['Produto']:
        return Produto.query.all()

    def atualizar(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class Item(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)
    cod_produto = db.Column(db.Integer, db.ForeignKey('produto.codigo'), nullable=False)
    cod_venda = db.Column(db.Integer, db.ForeignKey('venda.codigo'), nullable=False)
    qtde = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)

    @staticmethod
    def ler(codigo: int) -> Optional['Item']:
        return Item.query.get(codigo)

    @staticmethod
    def ler_todos() -> List['Item']:
        return Item.query.all()

    def atualizar(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

# Rotas
@app.route('/')
def index():
    try:
        produtos = Produto.query.all()
        return render_template('index.html', produtos=produtos)
    except Exception as e:
        flash(f"Erro ao acessar o banco de dados: {str(e)}", "error")
        return render_template('index.html', produtos=[])

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Erro ao criar tabelas: {str(e)}")
            print("Executando migrações...")
            from flask_migrate import upgrade
            upgrade()
    app.run(debug=True)