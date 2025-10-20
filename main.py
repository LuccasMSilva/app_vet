import os
import logging
import traceback
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort, jsonify
from sqlalchemy.orm import joinedload
from services import generate_token
# Importar extensões compartilhadas
from extensions import db, login_manager
import models
import services

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obter o diretório base do projeto
basedir = os.path.abspath(os.path.dirname(__file__))

# Criar a aplicação Flask
app = Flask(__name__, instance_path=os.path.join(basedir, 'instance'))

# Configuração da aplicação
app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-dificil'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'pets.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensões com a aplicação
db.init_app(app)
login_manager.init_app(app)

@app.errorhandler(Exception)
def handle_exception(e):
    from werkzeug.exceptions import NotFound
    # Log full traceback to file for offline inspection
    tb = traceback.format_exc()
    logger.error('Unhandled Exception:\n%s', tb)
    
    # Se for um erro 404, deixe o Flask/Werkzeug lidar com ele
    if isinstance(e, NotFound):
        return e

    # Em modo de depuração, permita que o Flask mostre a página de depuração padrão
    if app.debug:
        raise e
        
    # Caso contrário, retorne uma mensagem de erro genérica
    return render_template_string('<h1>Erro interno</h1><p>Ocorreu um erro no servidor. Verifique os logs.</p>'), 500


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(models.User, int(user_id))

# aliases locais para compatibilidade com o código existente
User = models.User
Clinic = models.Clinic
Animal = models.Animal

@app.route("/_routes")
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = urllib.parse.unquote(rule.rule)
        line = "{:50s} {:20s} {}".format(rule.endpoint, methods, url)
        output.append(line)

    return "<pre>" + "\\n".join(sorted(output)) + "</pre>"
# ----------------- ROTAS -----------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = db.session.get(User, session["user_id"])
    if not user:
        session.pop('user_id', None)
        session.pop("role", None)
        return redirect(url_for('login'))

    # === VISÃO DO ADMIN ===
    if user.role == 'admin':
        all_animals = Animal.query.options(joinedload(Animal.dono), joinedload(Animal.clinic)).order_by(Animal.id.desc()).all()
        
        # Dados para os gráficos (sem alterações)
        procedimentos = [animal.procedimento.lower() for animal in all_animals if animal.procedimento]
        procedimento_counts = {
            'castração': procedimentos.count('castração'),
            'consulta': procedimentos.count('consulta'),
            'vacinação': procedimentos.count('vacinação'),
            'outros': len([p for p in procedimentos if p not in ['castração', 'consulta', 'vacinação']])
        }
        status_counts = {
            'Concluído': len([a for a in all_animals if a.status == 'Concluído']),
            'Aguardando': len([a for a in all_animals if a.status != 'Concluído'])
        }

        return render_template_string('''
            <h1>Dashboard do Administrador</h1> <img src="{{ url_for('static', filename='logo_prefeitura.png') }}"
            <p>Bem-vindo, {{ user.username }}!</p>
            <a href="{{ url_for('logout') }}">Logout</a> | <a href="{{ url_for('manage_clinics') }}">Gerenciar Clínicas</a> | <a href="{{ url_for('reports') }}">Ver Relatórios</a>
            
            <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                <div style="width: 25%;"><canvas id="procedimentosChart"></canvas></div>
                <div style="width: 25%;"><canvas id="statusChart"></canvas></div>
            </div>
            
            <h2 style="margin-top: 20px;">Todos os Animais Cadastrados</h2>
            <table border="1" style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; text-align: left;">ID</th>
                        <th style="padding: 8px; text-align: left;">Nome</th>
                        <th style="padding: 8px; text-align: left;">Espécie</th>
                        <th style="padding: 8px; text-align: left;">Status</th>
                        <th style="padding: 8px; text-align: left;">Clínica</th>
                        <th style="padding: 8px; text-align: left;">Token</th>
                        <th style="padding: 8px; text-align: left;">Dono</th>
                    </tr>
                </thead>
                <tbody>
                    {% for animal in animals %}
                    <tr>
                       <td style="padding: 8px;">{{ animal.id }}</td>
                        <td style="padding: 8px;">{{ animal.nome }}</td>
                        <td style="padding: 8px;">{{ animal.especie }}</td>
                        <td style="padding: 8px;">{{ animal.status }}</td>
                        <td style="padding: 8px;">{{ animal.clinic.name if animal.clinic else 'N/A' }}</td>
                        <td style="padding: 8px;">{{ animal.verification_token or 'N/A' }}</td>
                        <td style="padding: 8px;">{{ animal.dono.username if animal.dono else 'N/A' }}</td>
                    </tr>
                    {% else %}
                    <tr><td colspan="6" style="text-align: center;">Nenhum animal cadastrado.</td></tr>
                    {% endfor %}
                </tbody>
            </table>

            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                // Script dos gráficos (sem alterações na lógica)
                const procedimentosCtx = document.getElementById('procedimentosChart').getContext('2d');
                new Chart(procedimentosCtx, {
                    type: 'pie',
                    data: {
                        labels: ['Castração', 'Consulta', 'Vacinação', 'Outros'],
                        datasets: [{
                            label: 'Tipos de Atendimento',
                            data: [{{ procedimento_counts.castração }}, {{ procedimento_counts.consulta }}, {{ procedimento_counts.vacinação }}, {{ procedimento_counts.outros }}],
                            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                        }]
                    }
                });

                const statusCtx = document.getElementById('statusChart').getContext('2d');
                new Chart(statusCtx, {
                    type: 'pie',
                    data: {
                        labels: ['Concluído', 'Aguardando'],
                        datasets: [{
                            label: 'Status dos Atendimentos',
                            data: [{{ status_counts.Concluído }}, {{ status_counts.Aguardando }}],
                            backgroundColor: ['#4CAF50', '#FF9800']
                        }]
                    }
                });
            </script>
        ''', user=user, animals=all_animals, procedimento_counts=procedimento_counts, status_counts=status_counts)

    # === VISÃO DA CLÍNICA ===
    elif user.role == 'clinic':
        return redirect(url_for('clinic_dashboard'))

    # === VISÃO DO TUTOR ===
    elif user.role == 'user' or user.role == 'tutor':
        user_animals = Animal.query.filter_by(dono_id=user.id).order_by(Animal.id.desc()).all()
        return render_template_string('''
            <h1>Seu Painel</h1>
            <p>Bem-vindo, {{ user.username }}!</p>
            <a href="{{ url_for('logout') }}">Logout</a> | <a href="{{ url_for('register_animal') }}">Cadastrar Novo Animal</a>
            <h2>Seus Animais Cadastrados</h2>
            {% if animals %}
                <table border="1">
                    <tr><th>ID</th><th>Nome</th><th>Espécie</th><th>Status</th><th>Token</th><th>Dono</th><th>Clínica</th></tr>
                    {% for animal in animals %}
                    <tr>
                        <td>{{ animal.id }}</td>
                        <td>{{ animal.nome }}</td>
                        <td>{{ animal.especie }}</td>
                        <td>{{ animal.status }}</td>
                        <td>{{ animal.verification_token or 'N/A' }}</td>
                        <td>{{ animal.dono.username if animal.dono else 'N/A' }}</td>
                        <td>{{ animal.clinic.name if animal.clinic else 'Aguardando atribuição' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>Você ainda não cadastrou nenhum animal.</p>
            {% endif %}
        ''', user=user, animals=user_animals)
    
    return "Tipo de usuário desconhecido."

@app.route("/claim_animal/<int:animal_id>", methods=["POST"])
def claim_animal(animal_id):
    if "user_id" not in session or session.get("role") != "clinic":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    animal = Animal.query.get_or_404(animal_id)

    if animal.clinic_id:
        flash("Este animal já foi reivindicado por outra clínica.", "warning")
    else:
        animal.clinic_id = user.clinic_id
        animal.status = "Aguardando agendamento"
        db.session.commit()
        flash(f"Você reivindicou o atendimento para {animal.nome}.", "success")
    
    return redirect(url_for("clinic_dashboard"))

@app.route("/clinic_dashboard")
def clinic_dashboard():
    if "user_id" not in session or session.get("role") != "clinic":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if not user or not user.clinic_id:
        flash("Usuário da clínica não associado a uma clínica.", "danger")
        return redirect(url_for("login"))

    # Animais já atribuídos a esta clínica
    clinic_animals = Animal.query.filter_by(clinic_id=user.clinic_id).order_by(Animal.id.desc()).all()
    
    # Animais disponíveis para serem reivindicados
    available_animals = Animal.query.filter_by(clinic_id=None).order_by(Animal.id.desc()).all()

    return render_template_string('''
        <h1>Painel da Clínica: {{ clinic_name }}</h1>
        <p>Bem-vindo, {{ user.username }}!</p>
        <a href="{{ url_for('logout') }}">Logout</a> | <a href="{{ url_for('reports') }}">Ver Relatórios</a>
        
        <h2>Seus Atendimentos</h2>
        <table border="1" style="width:100%">
            <thead>
                <tr><th>ID</th><th>Nome</th><th>Espécie</th><th>Procedimento</th><th>Status</th><th>Token</th><th>Ações</th></tr>
            </thead>
            <tbody>
                {% for animal in clinic_animals %}
                <tr>
                    <td>{{ animal.id }}</td>
                    <td>{{ animal.nome }}</td>
                    <td>{{ animal.especie }}</td>
                    <td>{{ animal.procedimento }}</td>
                    <td>{{ animal.status }}</td>
                    <td>{{ animal.verification_token or 'N/A' }}</td>
                    <td>
                        {% if animal.status == 'Aguardando agendamento' %}
                        <a href="{{ url_for('schedule', animal_id=animal.id) }}">Agendar</a>
                        {% elif animal.status == 'Agendado' %}
                        <form method="POST" action="{{ url_for('mark_as_complete', animal_id=animal.id) }}" style="display:inline;">
                            <button type="submit">Marcar como Concluído</button>
                        </form>
                        {% endif %}
                    </td>
</tr>
                {% else %}
                <tr><td colspan="6">Nenhum animal em atendimento.</td></tr>
                {% endfor %}
            </tbody>
        </table>

        <h2 style="margin-top: 20px;">Animais Disponíveis para Atendimento</h2>
        <table border="1" style="width:100%">
            <thead>
                <tr><th>ID</th><th>Nome</th><th>Espécie</th><th>Procedimento</th><th>Ações</th></tr>
            </thead>
            <tbody>
                {% for animal in available_animals %}
                <tr>
                    <td>{{ animal.id }}</td>
                    <td>{{ animal.nome }}</td>
                    <td>{{ animal.especie }}</td>
                    <td>{{ animal.procedimento }}</td>
                    <td>
                        <form method="POST" action="{{ url_for('claim_animal', animal_id=animal.id) }}" style="display:inline;">
                            <button type="submit">Reivindicar</button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="5">Nenhum animal disponível no momento.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    ''', user=user, clinic_name=user.clinic.name, clinic_animals=clinic_animals, available_animals=available_animals)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if services.get_user_by_username(username):
            flash("Usuário já existe!", "danger")
            return redirect(url_for("register"))
        services.create_user(username=username, password=password)
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
        try:
            username = request.form["username"]
            password = request.form["password"]
            remember = "remember" in request.form
            user = User.query.filter_by(username=username).first()
            # debug info to diagnose login issues
            try:
                print(f"[DEBUG] login attempt user_found={bool(user)}, username={username}, user_id={getattr(user,'id',None)}, role={getattr(user,'role',None)}")
            except Exception:
                print(f"[DEBUG] login attempt: user lookup performed for username={username}")
            if user and user.check_password(password):
                session["user_id"] = user.id
                session["role"] = user.role
                session.permanent = remember
                flash("Login realizado!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Credenciais inválidas", "danger")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print("--- Login error:\n", tb)
            flash("Ocorreu um erro durante o login. Verifique o log do servidor.", "danger")
    
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
    return redirect(url_for("login"))
    if "user_id" not in session or session.get("role") != "clinic":
        abort(403)

    user = db.session.get(User, session["user_id"])
    animal = Animal.query.get_or_404(animal_id)

    if animal.clinic_id is None:
        animal.clinic_id = user.clinic_id
        animal.status = "Aguardando Agendamento"
        # Gera o token de verificação
        animal.verification_token = services.generate_token()
        db.session.commit()
        flash(f"Animal {animal.nome} reivindicado com sucesso! Token: {animal.verification_token}", "success")
    else:
        flash("Este animal já foi reivindicado por outra clínica.", "warning")

    return redirect(url_for("dashboard"))



@app.route("/schedule/<int:animal_id>", methods=["GET", "POST"])
def schedule(animal_id):
    if "user_id" not in session or session.get("role") != "clinic":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))

    animal = Animal.query.get_or_404(animal_id)
    user = db.session.get(User, session["user_id"])

    if animal.clinic_id != user.clinic_id:
        flash("Este animal não pertence à sua clínica.", "danger")
        return redirect(url_for("clinic_dashboard"))

    if request.method == "POST":
        data_str = request.form.get("data_agendamento")
        if data_str:
            try:
                animal.data_agendamento = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')
                animal.status = "Agendado"
                animal.verification_token = generate_token()  # <-- CORREÇÃO AQUI
                db.session.commit()
                flash(f"Atendimento para {animal.nome} agendado! Token: {animal.verification_token}", "success")
                return redirect(url_for("clinic_dashboard"))
            except ValueError:
                flash("Formato de data inválido. Use o formato YYYY-MM-DDTHH:MM.", "danger")
        else:
            flash("A data de agendamento é obrigatória.", "danger")
        
        return redirect(url_for('schedule', animal_id=animal.id))

    return render_template_string('''
        <h2>Agendar Atendimento para {{ animal.nome }}</h2>
        <p><strong>Dono:</strong> {{ animal.dono.username }} | <strong>Contato:</strong> {{ animal.contato }}</p>
        <form method="POST">
            <label for="data_agendamento">Data e Hora do Agendamento:</label><br>
            <input type="datetime-local" id="data_agendamento" name="data_agendamento" required><br><br>
            <button type="submit">Agendar</button>
        </form>
        <a href="{{ url_for('clinic_dashboard') }}">Cancelar</a>
    ''', animal=animal)


@app.route("/mark_as_complete/<int:animal_id>", methods=["POST"])
def mark_as_complete(animal_id):
    if "user_id" not in session or session.get("role") != "clinic":
        abort(403)

    animal = Animal.query.get_or_404(animal_id)
    user = db.session.get(User, session["user_id"])

    if animal.clinic_id != user.clinic_id:
        flash("Este animal não pertence à sua clínica.", "danger")
        return redirect(url_for("dashboard"))

    animal.status = "Concluído"
    animal.token_validated = True
    db.session.commit()
    flash(f"Atendimento para {animal.nome} marcado como concluído.", "success")

    return redirect(url_for("dashboard"))
    
@app.route('/assign_clinic', methods=['POST'])
def assign_clinic():
    if 'user_id' not in session or db.session.get(User, session['user_id']).role != 'admin':
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for('login'))
    animal_id = request.form.get('animal_id')
    clinic_id = request.form.get('clinic_id')
    
    if not animal_id or not clinic_id:
        flash("Animal ou clínica inválida.", "danger")
        return redirect(url_for('dashboard'))

    animal = services.assign_clinic_to_animal(animal_id, clinic_id)
    if not animal:
        flash("Erro ao atribuir clínica.", "danger")
    else:
        flash(f"Clínica atribuída com sucesso para o animal {animal.nome}!", "success")

    return redirect(url_for('dashboard'))

@app.route('/_debug/users')
def _debug_users():
    # disponível apenas em modo debug local
    if not app.debug:
        abort(404)
    users = User.query.with_entities(User.id, User.username, User.role, User.email).all()
    return jsonify([{'id': u[0], 'username': u[1], 'role': u[2], 'email': u[3]} for u in users])


@app.route('/_debug/animals')
def _debug_animals():
    if not app.debug:
        abort(404)
    animals = Animal.query.with_entities(Animal.id, Animal.nome, Animal.status, Animal.verification_token, Animal.token_validated, Animal.data_agendamento).all()
    out = []
    for a in animals:
        out.append({'id': a[0], 'nome': a[1], 'status': a[2], 'token': a[3], 'token_validated': bool(a[4]), 'agendamento': str(a[5]) if a[5] else None})
    return jsonify(out)


@app.route('/_debug/current_user')
def _debug_current_user():
    if not app.debug:
        abort(404)
    data = {'session': dict(session)}
    uid = session.get('user_id')
    if uid:
        u = User.query.get(uid)
        data['user'] = {'id': u.id, 'username': u.username, 'role': u.role, 'clinic_id': u.clinic_id}
    return jsonify(data)


@app.route('/validate_token/<int:animal_id>', methods=['POST'])
def validate_token(animal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = db.session.get(User, session.get('user_id'))
    if not user or user.role not in ['clinic', 'admin']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))

    token = request.form.get('token')
    if not token:
        flash('Token obrigatório.', 'danger')
        return redirect(url_for('dashboard'))

    ok = services.validate_token(animal_id, token)
    if ok:
        flash('Token validado com sucesso.', 'success')
    else:
        flash('Token inválido.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/admin/clinics')
def admin_clinics():
    if 'user_id' not in session or db.session.get(User, session['user_id']).role != 'admin':
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for('login'))
    # List clinics from the Clinic model so admin sees the actual clinic records
    clinics = Clinic.query.all()
    return render_template_string('''
        <h1>Gerenciar Clínicas</h1>
        <a href="{{ url_for('dashboard') }}">Voltar ao Dashboard</a> | 
        <a href="{{ url_for('add_clinic') }}">Adicionar Nova Clínica</a>
        <hr>
        <table border="1">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nome da Clínica</th>
                    <th>Contato</th>
                </tr>
            </thead>
            <tbody>
                {% for clinic in clinics %}
                <tr>
                    <td>{{ clinic.id }}</td>
                    <td>{{ clinic.name }}</td>
                    <td>{{ clinic.contact }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    ''', clinics=clinics)

@app.route('/admin/add_clinic', methods=['GET', 'POST'])
def add_clinic():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        contact = request.form['contact']
        
        existing_clinic = Clinic.query.filter_by(name=username).first()
        if existing_clinic:
            flash('Clínica com esse nome já existe.', 'danger')
            return redirect(url_for('add_clinic'))
        # create the Clinic record
        clinic = services.create_clinic(name=username, contact=contact)
        # create the user account linked to clinic
        services.create_user(username=username, password=password, role='clinic', email=email, contact=contact, clinic_id=clinic.id)
        flash('Clínica adicionada com sucesso!', 'success')
        return redirect(url_for('admin_clinics'))

    return render_template_string('''
        <h1>Adicionar Nova Clínica</h1>
        <form method="post">
            <label for="username">Nome da Clínica:</label><br>
            <input type="text" id="username" name="username" required><br>
            
            <label for="email">Email:</label><br>
            <input type="email" id="email" name="email" required><br>
            
            <label for="password">Senha:</label><br>
            <input type="password" id="password" name="password" required><br>

            <label for="contact">Contato:</label><br>
            <input type="text" id="contact" name="contact" required><br>
            
            <input type="submit" value="Adicionar Clínica">
        </form>
        <br>
        <a href="{{ url_for('admin_clinics') }}">Cancelar</a>
    ''')



@app.route("/update_animal_status/<int:animal_id>", methods=["POST"])
def update_animal_status(animal_id):
    if "user_id" not in session or session["role"] != 'clinic':
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))

    animal = Animal.query.get_or_404(animal_id)
    user = User.query.get(session["user_id"])

    # Garante que o animal pertence à clínica que está tentando atualizá-lo
    if animal.clinic_id != user.clinic_id:
        flash("Você não tem permissão para atualizar este animal.", "danger")
        return redirect(url_for("dashboard"))

    new_status = request.form.get("status")
    if new_status == 'Concluído':
        services.mark_animal_complete(animal_id)
        flash(f"Status do animal {animal.nome} atualizado para {new_status}.", "success")
    else:
        flash("Status inválido.", "danger")

    return redirect(url_for("dashboard"))

@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    print(f"[DEBUG reports] session_user_id={session.get('user_id')} session_role={session.get('role')}")
    try:
        print(f"[DEBUG reports] user.id={user.id} user.role={user.role} user.clinic_id={user.clinic_id}")
    except Exception:
        print('[DEBUG reports] could not read user attributes')
    clinics_data = []
    clinic_data = None

    if user.role == 'admin':
        # Admin view: Group completed animals by clinic
        completed_animals = Animal.query.filter_by(status='Concluído').options(joinedload(Animal.clinic), joinedload(Animal.dono)).all()
        clinics_map = {}
        for animal in completed_animals:
            if animal.clinic:
                if animal.clinic.id not in clinics_map:
                    clinics_map[animal.clinic.id] = {'name': animal.clinic.name, 'animals': []}
                clinics_map[animal.clinic.id]['animals'].append(animal)
        clinics_data = list(clinics_map.values())
        print(f"[DEBUG reports] admin found {len(clinics_data)} clinics with completed animals")

    elif user.role == 'clinic' and user.clinic_id:
        # Clinic view: Show only their completed animals
        completed_animals = Animal.query.filter_by(status='Concluído', clinic_id=user.clinic_id).options(joinedload(Animal.dono)).all()
        print(f"[DEBUG reports] clinic completed_animals count = {len(completed_animals)} for clinic_id={user.clinic_id}")
        clinic_name = Clinic.query.get(user.clinic_id).name
        clinic_data = {'name': clinic_name, 'animals': completed_animals}

    template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Relatórios</title>
    </head>
    <body>
        <h1>Relatórios de Atendimentos Concluídos</h1>
        <a href="{{ url_for('dashboard') }}">Voltar para o Dashboard</a>
        <hr>

        {% if user.role == 'admin' %}
            <h2>Relatório Geral por Clínica</h2>
            {% for clinic in clinics_data %}
                <h3>{{ clinic.name }}</h3>
                {% if clinic.animals %}
                    <table border="1" style="width:100%;">
                        <tr>
                            <th>Animal</th>
                            <th>Espécie</th>
                            <th>Tutor</th>
                            <th>Procedimento</th>
                            <th>Data Agendamento</th>
                            <th>Token</th>
                        </tr>
                        {% for animal in clinic.animals %}
                        <tr>
                            <td>{{ animal.nome }}</td>
                            <td>{{ animal.especie }}</td>
                            <td>{{ animal.dono.username if animal.dono else 'N/A' }}</td>
                            <td>{{ animal.procedimento }}</td>
                            <td>{{ animal.agendamento }}</td>
                            <td>{{ animal.verification_token if animal.verification_token else '-' }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p>Nenhum atendimento concluído para esta clínica.</p>
                {% endif %}
            {% else %}
                <p>Nenhum atendimento concluído registrado.</p>
            {% endfor %}

        {% elif user.role == 'clinic' %}
            <h2>Relatório da Clínica: {{ clinic_data.name if clinic_data else '—' }}</h2>
            {% if clinic_data and clinic_data.animals %}
                <table border="1" style="width:100%;">
                    <tr>
                        <th>Animal</th>
                        <th>Espécie</th>
                        <th>Tutor</th>
                        <th>Procedimento</th>
                        <th>Data Agendamento</th>
                        <th>Token</th>
                    </tr>
                    {% for animal in clinic_data.animals %}
                    <tr>
                        <td>{{ animal.nome }}</td>
                        <td>{{ animal.especie }}</td>
                        <td>{% if user.role == 'admin' %}
                            <a href="{{ url_for('manage_clinics') }}">Gerenciar Clínicas</a>
                        {% endif %}
                        <td>{{ animal.procedimento }}</td>
                        <td>{{ animal.agendamento }}</td>
                        <td>{{ animal.verification_token if animal.verification_token else '-' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>Nenhum atendimento concluído para sua clínica.</p>
            {% endif %}
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(template, user=user, clinics_data=clinics_data, clinic_data=clinic_data)


# ----------------- ROTAS DE CLÍNICA (ADMIN) -----------------
@app.route("/clinics")
def manage_clinics():
    if "user_id" not in session:
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("dashboard"))
    
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
    if "user_id" not in session:
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("dashboard"))
    
    clinic = Clinic.query.get_or_404(clinic_id)
    db.session.delete(clinic)
    db.session.commit()
    flash("Clínica excluída com sucesso!", "success")
    return redirect(url_for("manage_clinics"))


@app.route('/register_animal', methods=['GET', 'POST'])
def register_animal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nome = request.form["nome"]
        especie = request.form["especie"]
        idade = request.form["idade"]
        contato = request.form["contato"]
        procedimento = request.form.get("procedimento")
        if procedimento == 'outros':
            procedimento = request.form.get('procedimento_outro', '').strip()

        if not all([nome, especie, idade, contato, procedimento]):
            flash("Por favor, preencha todos os campos.", "danger")
            return redirect(request.url)

        new_animal = Animal(
            nome=nome,
            especie=especie,
            idade=idade,
            contato=contato,
            procedimento=procedimento,
            dono_id=session["user_id"]
        )
        db.session.add(new_animal)
        db.session.commit()
        flash("Animal cadastrado com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template_string('''
        <h2>Cadastrar Novo Animal</h2>
        <form method="post">
            Nome: <input name="nome" required><br>
            Espécie: <input name="especie" required><br>
            Idade: <input name="idade" required><br>
            Contato: <input name="contato" required><br>
            
            <p>Selecione o serviço:</p>
            <input type="radio" id="castracao" name="procedimento" value="castração" required>
            <label for="castracao">Castração</label><br>
            
            <input type="radio" id="consulta" name="procedimento" value="consulta">
            <label for="consulta">Consulta</label><br>
            
            <input type="radio" id="vacinacao" name="procedimento" value="vacinação">
            <label for="vacinacao">Vacinação</label><br>
            
            <input type="radio" id="outros" name="procedimento" value="outros">
            <label for="outros">Outros:</label>
            <input type="text" name="procedimento_outro" placeholder="Especifique"><br><br>
            
            <button type="submit">Cadastrar</button>
        </form>
        <a href="{{ url_for('dashboard') }}">Voltar ao Painel</a>
    ''')
    return render_template_string('''
        <h1>Cadastrar Novo Animal</h1>
        <form method="post">
            <label for="name">Nome do Animal:</label><br>
            <input type="text" id="name" name="name" required><br>
            
            <label for="species">Espécie:</label><br>
            <input type="text" id="species" name="species" required><br>
            
            <label for="contato">Contato (Telefone):</label><br>
            <input type="text" id="contato" name="contato" required><br>
            
            <label for="procedimento">Procedimento Necessário:</label><br>
            <input type="text" id="procedimento" name="procedimento" required><br>
            
            <input type="submit" value="Cadastrar Animal">
        </form>
        <br>
        <a href="{{ url_for('dashboard') }}">Voltar ao Dashboard</a>
    ''')