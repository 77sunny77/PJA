import os
from datetime import datetime
from typing import Optional, List
import secrets

# Importando bibliotecas necessárias para o funcionamento do Flask e do banco de dados
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

#pip install -r requerimentos.txt

# Inicializando a aplicação Flask
app = Flask(__name__, template_folder='templates')

# Definindo a chave secreta da aplicação, que é usada para proteger sessões
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(16)

# Configurando o banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'loja.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializando o banco de dados e as migrações
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Classe base para operações comuns de CRUD (Criar, Ler, Atualizar, Deletar)
class ModeloBase:
    def criar(self):
        # Método para adicionar um objeto ao banco de dados
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()  # Reverte a transação em caso de erro
            raise e

    def deletar(self):
        # Método para remover um objeto do banco de dados
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()  # Reverte a transação em caso de erro
            raise e

# Definindo o modelo de dados para o Departamento
class Departamento(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)  # Código único do departamento
    nome = db.Column(db.String(50), nullable=False)  # Nome do departamento
    produtos = db.relationship('Produto', backref='departamento', lazy=True)  # Relacionamento com produtos

# Definindo o modelo de dados para o Produto
class Produto(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)  # Código único do produto
    nome = db.Column(db.String(50), nullable=False)  # Nome do produto
    descricao = db.Column(db.String(200))  # Descrição do produto
    preco_compra = db.Column(db.Float, nullable=False)  # Preço de compra do produto
    preco_venda = db.Column(db.Float, nullable=False)  # Preço de venda do produto
    qtd_estoque = db.Column(db.Integer, nullable=False, default=0)  # Quantidade em estoque
    uni_compra = db.Column(db.Integer, nullable=False)  # Unidade de compra
    uni_venda = db.Column(db.Integer, nullable=False)  # Unidade de venda
    cod_departamento = db.Column(db.Integer, db.ForeignKey('departamento.codigo'), nullable=False)  # Chave estrangeira para departamento
    itens = db.relationship('Item', backref='produto', lazy=True)  # Relacionamento com itens

# Definindo o modelo de dados para a Venda
class Venda(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)  # Código único da venda
    data = db.Column(db.DateTime, default=datetime.utcnow)  # Data da venda
    itens_venda = db.relationship('ItemVenda', backref='venda', lazy=True)  # Relacionamento com itens de venda

# Definindo o modelo de dados para o Item
class Item(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)  # Código único do item
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.codigo'), nullable=False)  # Chave estrangeira para produto
    quantidade = db.Column(db.Integer, nullable=False)  # Quantidade do item
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.codigo'), nullable=True)  # Chave estrangeira para venda

# Definindo o modelo de dados para o ItemVenda
class ItemVenda(db.Model, ModeloBase):
    codigo = db.Column(db.Integer, primary_key=True)  # Código único do item de venda
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.codigo'), nullable=False)  # Chave estrangeira para venda
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.codigo'), nullable=False)  # Chave estrangeira para produto
    quantidade = db.Column(db.Integer, nullable=False)  # Quantidade do item de venda
    preco_unitario = db.Column(db.Float, nullable=False)  # Preço unitário do item de venda

# Definindo o modelo de dados para o Usuário
class Usuario(db.Model, ModeloBase):
    id = db.Column(db.Integer, primary_key=True)  # ID único do usuário
    nome = db.Column(db.String(100), nullable=False)  # Nome do usuário
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email único do usuário
    senha_hash = db.Column(db.String(200), nullable=False)  # Senha do usuário (hash)

# Decorador para proteger rotas que requerem login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:  # Verifica se o usuário está logado
            flash('Por favor, faça login para acessar esta página.')  # Mensagem de erro
            return redirect(url_for('login'))  # Redireciona para a página de login
        return f(*args, **kwargs)  # Chama a função original se o usuário estiver logado
    return decorated_function

# Rota principal da aplicação
@app.route('/')
def index():
    try:
        pesquisa = request.args.get('pesquisa', '').strip()  # Obtém a pesquisa do usuário
        if pesquisa:
            # Filtra produtos com base na pesquisa
            produtos = Produto.query.filter(
                db.or_(
                    Produto.nome.ilike(f'%{pesquisa}%'),  # Nome do produto
                    Produto.descricao.ilike(f'%{pesquisa}%')  # Descrição do produto
                )
            ).all()
        else:
            produtos = Produto.query.all()  # Obtém todos os produtos se não houver pesquisa
        
        return render_template('index.html', produtos=produtos)  # Renderiza a página com os produtos
    except Exception as e:
        flash(f"Erro ao acessar o banco de dados: {str(e)}", "error")  # Mensagem de erro
        return render_template('index.html', produtos=[])

# Rota para buscar produtos via AJAX
@app.route('/buscar_produtos')
def buscar_produtos():
    try:
        pesquisa = request.args.get('pesquisa', '').strip()  # Obtém a pesquisa do usuário
        if pesquisa:
            produtos = Produto.query.filter(
                db.or_(
                    Produto.nome.ilike(f'%{pesquisa}%'),  # Nome do produto
                    Produto.descricao.ilike(f'%{pesquisa}%')  # Descrição do produto
                )
            ).all()
        else:
            produtos = Produto.query.all()  # Obtém todos os produtos se não houver pesquisa

        # Cria uma lista de produtos em formato JSON
        produtos_json = [{
            'codigo': p.codigo,
            'nome': p.nome,
            'descricao': p.descricao,
            'preco_venda': float(p.preco_venda)
        } for p in produtos]

        return jsonify({'produtos': produtos_json})  # Retorna os produtos em formato JSON
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Retorna erro em formato JSON

# Rota para adicionar um produto ao carrinho
@app.route('/adicionar_ao_carrinho', methods=['POST'])
def adicionar_ao_carrinho():
    try:
        produto_id = request.json.get('produto_id')  # Obtém o ID do produto do corpo da requisição
        if not produto_id:
            return jsonify({'error': 'ID do produto não fornecido'}), 400  # Retorna erro se o ID não for fornecido

        produto = Produto.query.get(produto_id)  # Busca o produto no banco de dados
        if not produto:
            return jsonify({'error': 'Produto não encontrado'}), 404  # Retorna erro se o produto não for encontrado

        if 'carrinho' not in session:
            session['carrinho'] = {}  # Inicializa o carrinho se não existir
        
        produto_id_str = str(produto_id)  # Converte o ID do produto para string
        if produto_id_str in session['carrinho']:
            session['carrinho'][produto_id_str] += 1  # Incrementa a quantidade se o produto já estiver no carrinho
        else:
            session['carrinho'][produto_id_str] = 1  # Adiciona o produto ao carrinho
        
        session.modified = True  # Marca a sessão como modificada
        
        return jsonify({
            'success': True,
            'cart_count': sum(session['carrinho'].values()),  # Total de itens no carrinho
            'message': 'Produto adicionado ao carrinho'  # Mensagem de sucesso
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Retorna erro em formato JSON

# Rota para exibir o carrinho
@app.route('/carrinho')
@login_required
def carrinho():
    try:
        if 'carrinho' not in session:
            session['carrinho'] = {}  # Inicializa o carrinho se não existir
        
        produtos_carrinho = []  # Lista para armazenar produtos no carrinho
        total = 0  # Inicializa o total
        
        for produto_id, quantidade in session['carrinho'].items():
            produto = Produto.query.get(int(produto_id))  # Busca o produto no banco de dados
            if produto:
                subtotal = produto.preco_venda * quantidade  # Calcula o subtotal
                produtos_carrinho.append({
                    'produto': produto,
                    'quantidade': quantidade,
                    'subtotal': subtotal
                })
                total += subtotal  # Atualiza o total
        
        return render_template('carrinho.html', 
                             produtos=produtos_carrinho, 
                             total=total)  # Renderiza a página do carrinho
    except Exception as e:
        flash(f"Erro ao acessar o carrinho: {str(e)}", "error")  # Mensagem de erro
        return redirect(url_for('index'))  # Redireciona para a página inicial

# Rota para atualizar a quantidade de um produto no carrinho
@app.route('/atualizar_quantidade', methods=['POST'])
def atualizar_quantidade():
    try:
        produto_id = str(request.json.get('produto_id'))  # Obtém o ID do produto
        quantidade = int(request.json.get('quantidade'))  # Obtém a nova quantidade
        
        if quantidade < 1:
            return jsonify({'error': 'Quantidade inválida'}), 400  # Retorna erro se a quantidade for inválida
            
        if 'carrinho' in session and produto_id in session['carrinho']:
            session['carrinho'][produto_id] = quantidade  # Atualiza a quantidade no carrinho
            session.modified = True  # Marca a sessão como modificada
            
            total = 0  # Inicializa o total
            for pid, qtd in session['carrinho'].items():
                produto = Produto.query.get(int(pid))  # Busca o produto no banco de dados
                if produto:
                    total += produto.preco_venda * qtd  # Atualiza o total
                    
            return jsonify({
                'success': True,
                'total': f"R$ {total:.2f}",  # Total formatado
                'subtotal': f"R$ {(Produto.query.get(int(produto_id)).preco_venda * quantidade):.2f}",  # Subtotal formatado
                'cart_count': sum(session['carrinho'].values())  # Total de itens no carrinho
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Retorna erro em formato JSON

# Rota para remover um item do carrinho
@app.route('/remover_item', methods=['POST'])
def remover_item():
    try:
        produto_id = str(request.json.get('produto_id'))  # Obtém o ID do produto
        
        if 'carrinho' in session and produto_id in session['carrinho']:
            del session['carrinho'][produto_id]  # Remove o produto do carrinho
            session.modified = True  # Marca a sessão como modificada
            
            total = 0  # Inicializa o total
            for pid, qtd in session['carrinho'].items():
                produto = Produto.query.get(int(pid))  # Busca o produto no banco de dados
                if produto:
                    total += produto.preco_venda * qtd  # Atualiza o total
                    
            return jsonify({
                'success': True,
                'total': f"R$ {total:.2f}",  # Total formatado
                'cart_count': sum(session['carrinho'].values())  # Total de itens no carrinho
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Retorna erro em formato JSON

# Rota para finalizar a compra
@app.route('/finalizar_compra', methods=['POST'])
def finalizar_compra():
    try:
        if 'carrinho' not in session or not session['carrinho']:
            return jsonify({'error': 'Carrinho vazio'}), 400  # Retorna erro se o carrinho estiver vazio

        total = 0  # Inicializa o total
        itens_venda = []  # Lista para armazenar itens da venda
        
        for produto_id, quantidade in session['carrinho'].items():
            produto = Produto.query.get(int(produto_id))  # Busca o produto no banco de dados
            if produto:
                if produto.qtd_estoque < quantidade:
                    return jsonify({
                        'error': f'Quantidade insuficiente em estoque para {produto.nome}'  # Retorna erro se não houver estoque suficiente
                    }), 400
                    
                subtotal = produto.preco_venda * quantidade  # Calcula o subtotal
                total += subtotal  # Atualiza o total
                itens_venda.append({
                    'produto': produto,
                    'quantidade': quantidade,
                    'preco_unitario': produto.preco_venda  # Armazena informações do item de venda
                })

        for item in itens_venda:
            produto = item['produto']
            produto.qtd_estoque -= item['quantidade']  # Atualiza o estoque do produto
            produto.criar()  # Salva as alterações no banco de dados

        session['carrinho'] = {}  # Limpa o carrinho após a compra
        session.modified = True  # Marca a sessão como modificada
        
        return jsonify({
            'success': True,
            'message': 'Compra finalizada com sucesso!',  # Mensagem de sucesso
            'total': f"R$ {total:.2f}"  # Total formatado
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Retorna erro em formato JSON

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')  # Obtém o email do formulário
        senha = request.form.get('senha')  # Obtém a senha do formulário
        
        usuario = Usuario.query.filter_by(email=email).first()  # Busca o usuário no banco de dados
        
        if usuario and check_password_hash(usuario.senha_hash, senha):  # Verifica se o usuário existe e a senha está correta
            session['usuario_id'] = usuario.id  # Armazena o ID do usuário na sessão
            session['usuario_nome'] = usuario.nome  # Armazena o nome do usuário na sessão
            flash('Login realizado com sucesso!')  # Mensagem de sucesso
            return redirect(url_for('index'))  # Redireciona para a página inicial
        
        flash('Email ou senha incorretos.')  # Mensagem de erro
    
    return render_template('login.html')  # Renderiza a página de login

# Rota para cadastro de novos usuários
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')  # Obtém o nome do formulário
        email = request.form.get('email')  # Obtém o email do formulário
        senha = request.form.get('senha')  # Obtém a senha do formulário
        confirmar_senha = request.form.get('confirmar_senha')  # Obtém a confirmação da senha
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem.')  # Mensagem de erro se as senhas não coincidirem
            return render_template('cadastro.html')  # Renderiza a página de cadastro
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.')  # Mensagem de erro se o email já estiver cadastrado
            return render_template('cadastro.html')  # Renderiza a página de cadastro
        
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha)  # Gera o hash da senha
        )
        
        try:
            novo_usuario.criar()  # Salva o novo usuário no banco de dados
            flash('Cadastro realizado com sucesso! Faça login para continuar.')  # Mensagem de sucesso
            return redirect(url_for('login'))  # Redireciona para a página de login
        except Exception as e:
            flash('Erro ao realizar cadastro. Tente novamente.')  # Mensagem de erro
            
    return render_template('cadastro.html')  # Renderiza a página de cadastro

# Rota para logout
@app.route('/logout')
def logout():
    session.clear()  # Limpa a sessão do usuário
    flash('Você foi desconectado.')  # Mensagem de sucesso
    return redirect(url_for('index'))  # Redireciona para a página inicial

# Inicializa a aplicação e cria o banco de dados se necessário
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()  # Cria todas as tabelas do banco de dados
            
            # Adiciona produtos de exemplo ao banco de dados
            for i in range(1, 9):
                nome_produto = f'produto{i}'
                if not Produto.query.filter_by(nome=nome_produto).first():
                    novo_produto = Produto(
                        nome=nome_produto,
                        descricao=f'Descrição do {nome_produto}',
                        preco_compra=1.50 * i,
                        preco_venda=2.00 * i,
                        qtd_estoque=100,
                        uni_compra=1,
                        uni_venda=1,
                        cod_departamento=1
                    )
                    novo_produto.criar()  # Salva o novo produto no banco de dados
                    print(f"Produto '{nome_produto}' adicionado ao banco de dados.")  # Mensagem de confirmação
        except Exception as e:
            print(f"Erro ao criar tabelas: {str(e)}")  # Mensagem de erro ao criar tabelas
            print("Executando migrações...")  # Mensagem de migração
            from flask_migrate import upgrade
            upgrade()  # Executa migrações se necessário
    app.run(debug=True)  # Inicia a aplicação em modo de depuração
