from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from backend.extensions import db, login_manager
from backend.models import User
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        contato = request.form.get("contato")
        
        # Validações
        if not all([username, email, password, confirm_password, contato]):
            flash("Todos os campos são obrigatórios", "error")
            return render_template("auth/register.html")
        
        if password != confirm_password:
            flash("As senhas não coincidem", "error")
            return render_template("auth/register.html")
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            flash("Nome de usuário já existe", "error")
            return render_template("auth/register.html")
        
        if User.query.filter_by(email=email).first():
            flash("Email já cadastrado", "error")
            return render_template("auth/register.html")
        
        # Criar novo usuário
        user = User(
            username=username,
            email=email,
            contato=contato,
            role='user'  # papel padrão para dono de pet
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash("Cadastro realizado com sucesso! Faça login para continuar.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao criar conta. Tente novamente.", "error")
            return render_template("auth/register.html")
    
    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["role"] = user.role
            return redirect(url_for("dashboard.index"))
        
        flash("Usuário ou senha inválidos", "error")
    
    # Referencia explícita ao template dentro da pasta auth
    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("role", None)
    return redirect(url_for("auth.login"))