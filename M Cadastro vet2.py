import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

app = Flask(__name__)
app.secret_key = "supersegredo"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(instance_path, "pets.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

db = SQLAlchemy(app)

# ----------------- MODELOS -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' | 'clinic' | 'admin'
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)
    clinic = db.relationship('Clinic', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(100), nullable=False)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    especie = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    contato = db.Column(db.String(100), nullable=False)
    procedimento = db.Column(db.String(200), nullable=True)
    dono_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=True)
    agendamento = db.Column(db.String(100), nullable=True)

# ----------------- ROTAS -----------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe!", "danger")
            return redirect(url_for("register"))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("login"))
    return render_template_string("""
        <h2>Cadastro</h2>
        <form method="post">
            Usuário: <input name="username"><br>
            Senha: <input type="password" name="password"><br>
            <button type="submit">Cadastrar</button>
        </form>
        <a href="{{ url_for('login') }}">Já tem conta? Login</a>
    """)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        remember = "remember" in request.form
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = user.role
            session.permanent = remember
            flash("Login realizado!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciais inválidas", "danger")
    
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Sistema Veterinário</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f0f2f5;
                }
                .container {
                    max-width: 400px;
                    margin: 50px auto;
                    padding: 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .partners {
                    text-align: center;
                    margin-bottom: 20px;
                }
                .partner-logos {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 20px;
                    margin-bottom: 20px;
                }
                .partner-logos img {
                    max-width: 45%;
                    height: auto;
                    object-fit: contain;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                input[type="text"],
                input[type="password"] {
                    width: 100%;
                    padding: 8px;
                    margin: 5px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                button {
                    width: 100%;
                    padding: 10px;
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #0052a3;
                }
                .links {
                    text-align: center;
                    margin-top: 15px;
                }
                .links a {
                    color: #0066cc;
                    text-decoration: none;
                }
                .links a:hover {
                    text-decoration: underline;
                }
                .remember-me {
                    margin: 10px 0;
                }
                .flash-messages {
                    margin-bottom: 20px;
                }
                .flash-message {
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                .flash-message.success {
                    background-color: #d4edda;
                    color: #155724;
                }
                .flash-message.danger {
                    background-color: #f8d7da;
                    color: #721c24;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Sistema de Gerenciamento Veterinário</h2>
                </div>
                
                <div class="partners">
                    <h3>Uma parceria</h3>
                    <div class="partner-logos">
                        <img src="{{ url_for('static', filename='logo_prefeitura.png') }}" 
                             alt="Prefeitura de Maricá" 
                             title="Prefeitura de Maricá">
                        <img src="{{ url_for('static', filename='logo_ictim.png') }}" 
                             alt="ICTIM" 
                             title="Instituto de Ciência, Tecnologia e Inovação de Maricá">
                    </div>
                </div>

                <div class="flash-messages">
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="flash-message {{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                </div>

                <form method="post">
                    <div class="form-group">
                        <input type="text" name="username" placeholder="Nome de usuário" required>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" placeholder="Senha" required>
                    </div>
                    <div class="remember-me">
                        <label>
                            <input type="checkbox" name="remember"> Lembrar-me
                        </label>
                    </div>
                    <button type="submit">Entrar</button>
                </form>

                <div class="links">
                    <a href="{{ url_for('register') }}">Não tem conta? Cadastre-se</a>
                </div>
            </div>
        </body>
        </html>
    """)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    animais = []
    animais_agendados_clinica = [] # Para a lista específica da clínica logada

    if session["role"] in ["admin"]:
        animais = Animal.query.all()
    elif session["role"] == "clinic":
        if user.clinic_id:
            # Animais disponíveis (sem clínica)
            animais = Animal.query.filter(Animal.clinic_id.is_(None)).all()
            # Animais já agendados para esta clínica
            animais_agendados_clinica = Animal.query.filter_by(clinic_id=user.clinic_id).all()
        else:
            flash("Este usuário de clínica não está associado a nenhuma entidade clínica.", "warning")
    else: # user role
        animais = Animal.query.filter_by(dono_id=user.id).all()
    
    clinics = Clinic.query.all() if session["role"] in ['admin', 'clinic'] else []
    
    return render_template_string("""
        <h2>Bem-vindo, {{ user.username }}!</h2>
        {% if session.role == 'admin' %}<p>Você é ADMINISTRADOR</p>{% endif %}
        {% if session.role == 'clinic' %}<p>Você representa a: <b>{{ user.clinic.name if user.clinic else 'Clínica não associada' }}</b></p>{% endif %}
        <a href="{{ url_for('logout') }}">Sair</a><br><br>

        {% if session.role == 'admin' %}
        <a href="{{ url_for('manage_clinics') }}">Gerenciar Clínicas</a><br><br>
        {% endif %}

        {# Bloco para Admin #}
        {% if session.role == 'admin' %}
        <h3>Visão Geral de Todos os Animais</h3>
        <table border="1" style="width:100%; text-align:left;">
            <tr>
                <th>ID</th>
                <th>Nome</th>
                <th>Espécie</th>
                <th>Procedimento</th>
                <th>Status</th>
            </tr>
            {% for a in animais %}
            <tr>
                <td>{{ a.id }}</td>
                <td>{{ a.nome }}</td>
                <td>{{ a.especie }}</td>
                <td>{{ a.procedimento or 'N/A' }}</td>
                <td>
                    {% if a.clinic %}
                        Agendado em {{ a.clinic.name }} para {{ a.agendamento or 'data não definida' }}
                    {% else %}
                        <b style="color:green;">Aguardando agendamento</b>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5">Nenhum animal cadastrado no sistema.</td></tr>
            {% endfor %}
        </table>
        <hr>
        
        {# Bloco para Clínica #}
        {% elif session.role == 'clinic' %}
        <h3>Animais Agendados na sua Clínica</h3>
        <ul>
        {% for a in animais_agendados_clinica %}
            <li><b>ID: {{ a.id }}</b> - {{ a.nome }} ({{ a.especie }}) - Agendado para: {{ a.agendamento or 'Não definido' }}</li>
        {% else %}
            <li>Nenhum animal agendado para sua clínica no momento.</li>
        {% endfor %}
        </ul>
        <hr>
        <h3>Animais Aguardando Agendamento</h3>
        <p>Abaixo estão os animais que podem ser agendados para a sua clínica.</p>
        <table border="1" style="width:100%; text-align:left;">
            <tr><th>ID</th><th>Nome</th><th>Espécie</th><th>Procedimento</th></tr>
            {% for a in animais %}
            <tr>
                <td>{{ a.id }}</td>
                <td>{{ a.nome }}</td>
                <td>{{ a.especie }}</td>
                <td>{{ a.procedimento or 'N/A' }}</td>
            </tr>
            {% else %}
            <tr><td colspan="4">Nenhum animal aguardando agendamento.</td></tr>
            {% endfor %}
        </table>
        
        {# Bloco para Usuário comum #}
        {% else %}
        <h3>Seus animais cadastrados</h3>
        <ul>
        {% for a in animais %}
            <li><b>ID: {{ a.id }}</b> - {{ a.nome }} - {{ a.especie }} - {{ a.idade }} anos - Procedimento: {{ a.procedimento or 'N/A' }} - Agendamento: {{ a.agendamento or 'N/A' }} - Clínica: {{ a.clinic.name if a.clinic else 'Não atribuída' }}</li>
        {% else %}
            <li>Você ainda não cadastrou nenhum animal.</li>
        {% endfor %}
        </ul>
        {% endif %}

        {% if session.role == 'user' %}<a href="{{ url_for('add_animal') }}">Cadastrar novo animal</a>{% endif %}

        {% if session.role in ['admin', 'clinic'] %}
        <h3>Atribuir Clínica e Agendar Procedimento</h3>
        <form method="post" action="{{ url_for('schedule') }}">
            Animal ID: <input name="animal_id" type="number" required><br>
            
            {% if session.role == 'clinic' and user.clinic %}
                <input type="hidden" name="clinic_id" value="{{ user.clinic_id }}">
                Agendando para sua clínica: <b>{{ user.clinic.name }}</b><br>
            {% else %}
                Clínica: <select name="clinic_id" required>
                    <option value="">Selecione uma clínica</option>
                {% for c in clinics %}
                    <option value="{{ c.id }}">{{ c.name }}</option>
                {% endfor %}
                </select><br>
            {% endif %}

            Data/horário: <input name="agendamento" placeholder="YYYY-MM-DD HH:MM"><br>
            <button type="submit">Agendar</button>
        </form>
        {% endif %}
    """, user=user, animais=animais, clinics=clinics, animais_agendados_clinica=animais_agendados_clinica)

@app.route("/add_animal", methods=["GET", "POST"])
def add_animal():
    if "user_id" not in session or session["role"] != "user":
        flash("Apenas usuários podem cadastrar animais.", "danger")
        return redirect(url_for("login"))
    if request.method == "POST":
        nome = request.form["nome"]
        especie = request.form["especie"]
        idade = int(request.form["idade"])
        contato = request.form["contato"]
        procedimento = request.form.get("procedimento")
        animal = Animal(nome=nome, especie=especie, idade=idade, contato=contato, procedimento=procedimento, dono_id=session["user_id"])
        db.session.add(animal)
        db.session.commit()
        flash("Animal cadastrado com sucesso!", "success")
        return redirect(url_for("dashboard"))
    return render_template_string("""
        <h2>Cadastrar Animal</h2>
        <form method="post">
            Nome: <input name="nome"><br>
            Espécie: <input name="especie"><br>
            Idade: <input type="number" name="idade"><br>
            Contato: <input name="contato"><br>
            Procedimento: <input name="procedimento"><br>
            <button type="submit">Salvar</button>
        </form>
        <a href="{{ url_for('dashboard') }}">Voltar</a>
    """)

@app.route("/schedule", methods=["POST"])
def schedule():
    if "user_id" not in session or session["role"] not in ['admin', 'clinic']:
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    animal_id = request.form.get("animal_id")
    clinic_id = request.form.get("clinic_id")
    
    # Validação para usuário de clínica
    if session['role'] == 'clinic' and user.clinic_id and int(clinic_id) != user.clinic_id:
        flash("Você só pode agendar para sua própria clínica.", "danger")
        return redirect(url_for('dashboard'))

    agendamento = request.form["agendamento"]
    animal = Animal.query.get(animal_id)
    if animal:
        animal.clinic_id = clinic_id
        animal.agendamento = agendamento
        db.session.commit()
        flash("Agendamento realizado com sucesso!", "success")
    else:
        flash("Animal não encontrado", "danger")
    return redirect(url_for("dashboard"))

# ----------------- ROTAS DE CLÍNICA (ADMIN) -----------------
@app.route("/clinics")
def manage_clinics():
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))
    
    clinics = Clinic.query.all()
    return render_template_string("""
        <h2>Gerenciar Clínicas</h2>
        <a href="{{ url_for('add_clinic') }}">Adicionar Nova Clínica</a>
        <br><br>
        <table border="1">
            <tr>
                <th>ID</th>
                <th>Nome</th>
                <th>Contato</th>
                <th>Ações</th>
            </tr>
            {% for clinic in clinics %}
            <tr>
                <td>{{ clinic.id }}</td>
                <td>{{ clinic.name }}</td>
                <td>{{ clinic.contact }}</td>
                <td>
                    <a href="{{ url_for('edit_clinic', clinic_id=clinic.id) }}">Editar</a>
                    <form method="post" action="{{ url_for('delete_clinic', clinic_id=clinic.id) }}" style="display:inline;">
                        <button type="submit" onclick="return confirm('Tem certeza que deseja excluir?');">Excluir</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
        <br>
        <a href="{{ url_for('dashboard') }}">Voltar ao Painel</a>
    """, clinics=clinics)

@app.route("/add_clinic", methods=["GET", "POST"])
def add_clinic():
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        name = request.form["name"]
        contact = request.form["contact"]
        new_clinic = Clinic(name=name, contact=contact)
        db.session.add(new_clinic)
        db.session.commit()
        flash("Clínica adicionada com sucesso!", "success")
        return redirect(url_for("manage_clinics"))

    return render_template_string("""
        <h2>Adicionar Nova Clínica</h2>
        <form method="post">
            Nome: <input name="name" required><br>
            Contato: <input name="contact" required><br>
            <button type="submit">Salvar</button>
        </form>
        <a href="{{ url_for('manage_clinics') }}">Cancelar</a>
    """)

@app.route("/edit_clinic/<int:clinic_id>", methods=["GET", "POST"])
def edit_clinic(clinic_id):
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))
    
    clinic = Clinic.query.get_or_404(clinic_id)

    if request.method == "POST":
        clinic.name = request.form["name"]
        clinic.contact = request.form["contact"]
        db.session.commit()
        flash("Clínica atualizada com sucesso!", "success")
        return redirect(url_for("manage_clinics"))

    return render_template_string("""
        <h2>Editar Clínica</h2>
        <form method="post">
            Nome: <input name="name" value="{{ clinic.name }}" required><br>
            Contato: <input name="contact" value="{{ clinic.contact }}" required><br>
            <button type="submit">Salvar Alterações</button>
        </form>
        <a href="{{ url_for('manage_clinics') }}">Cancelar</a>
    """, clinic=clinic)

@app.route("/delete_clinic/<int:clinic_id>", methods=["POST"])
def delete_clinic(clinic_id):
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))
    
    clinic = Clinic.query.get_or_404(clinic_id)
    db.session.delete(clinic)
    db.session.commit()
    flash("Clínica excluída com sucesso!", "success")
    return redirect(url_for("manage_clinics"))

# ----------------- MAIN -----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Adicionar dados iniciais (admin, clínicas) se não existirem
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)

        if not Clinic.query.first():
            clinic1 = Clinic(name='Clínica Vet 1', contact='111-111')
            clinic2 = Clinic(name='Clínica Vet 2', contact='222-222')
            db.session.add_all([clinic1, clinic2])
            db.session.commit()

        if not User.query.filter_by(username='clinic_user').first():
            clinic_for_user = Clinic.query.first()
            if clinic_for_user:
                clinic_user = User(username='clinic_user', role='clinic', clinic_id=clinic_for_user.id)
                clinic_user.set_password('clinic')
                db.session.add(clinic_user)

        db.session.commit()

    app.run(debug=True)