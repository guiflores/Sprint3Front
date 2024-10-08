from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room
import csv
import os
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Arquivo CSV para registrar os usuários e senhas
USERS_FILE = 'usuarios_senhas.csv'

# Função para carregar os usuários
def carregar_usuarios():
    if not os.path.exists(USERS_FILE):
        return {}
    
    usuarios = {}
    with open(USERS_FILE, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            nome, senha_hash = row
            usuarios[nome] = senha_hash
    return usuarios

# Função para salvar um novo usuário
def salvar_usuario(nome, senha_hash):
    with open(USERS_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([nome, senha_hash])

# Rota para a página de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']

        # Carregar usuários existentes
        usuarios = carregar_usuarios()

        # Verificar se o usuário já existe
        if nome in usuarios:
            senha_hash = usuarios[nome].encode('utf-8')
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash):
                session['nome'] = nome
                return redirect(url_for('chat'))
            else:
                return "Senha incorreta!", 401
        else:
            # Se o usuário for novo, cadastrar e salvar a senha hashada
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
            salvar_usuario(nome, senha_hash.decode('utf-8'))
            session['nome'] = nome
            return redirect(url_for('chat'))
    return render_template('login.html')

# Rota para a página de chat
@app.route('/chat')
def chat():
    if 'nome' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', nome=session['nome'])

# Evento de conexão ao socket
@socketio.on('join')
def handle_join(data):
    nome = session.get('nome')
    room = data['room']
    join_room(room)
    socketio.emit('message', {'msg': f"{nome} entrou no chat!"}, room=room)

# Evento de envio de mensagens
@socketio.on('message')
def handle_message(data):
    room = data['room']
    nome = session.get('nome')
    socketio.emit('message', {'msg': f"{nome}: {data['msg']}"}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
