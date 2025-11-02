from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.extensions import db
from backend.models import Clinic, User

clinics_bp = Blueprint('clinics', __name__)

@clinics_bp.route("/clinics")
def list_clinics():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    clinics = Clinic.query.all()
    return render_template("clinics/list.html", clinics=clinics)

@clinics_bp.route("/clinics/add", methods=["GET", "POST"])
def add_clinic():
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso negado", "error")
        return redirect(url_for("clinics.list_clinics"))
    
    if request.method == "POST":
        # Criar usuário para a clínica
        user = User(
            username=request.form["username"],
            role="clinic"
        )
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.flush()  # Para obter o ID do usuário
        
        # Criar a clínica
        clinic = Clinic(
            nome=request.form["nome"],
            endereco=request.form["endereco"],
            telefone=request.form["telefone"],
            user_id=user.id
        )
        db.session.add(clinic)
        db.session.commit()
        
        flash("Clínica adicionada com sucesso!")
        return redirect(url_for("clinics.list_clinics"))
    
    return render_template("clinics/add.html")

@clinics_bp.route("/clinics/<int:id>/edit", methods=["GET", "POST"])
def edit_clinic(id):
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso negado", "error")
        return redirect(url_for("clinics.list_clinics"))
    
    clinic = Clinic.query.get_or_404(id)
    
    if request.method == "POST":
        clinic.nome = request.form["nome"]
        clinic.endereco = request.form["endereco"]
        clinic.telefone = request.form["telefone"]
        
        db.session.commit()
        flash("Clínica atualizada com sucesso!")
        return redirect(url_for("clinics.list_clinics"))
    
    return render_template("clinics/edit.html", clinic=clinic)

@clinics_bp.route("/clinics/<int:id>/delete", methods=["POST"])
def delete_clinic(id):
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso negado", "error")
        return redirect(url_for("clinics.list_clinics"))
    
    clinic = Clinic.query.get_or_404(id)
    
    # Remover o usuário associado à clínica
    if clinic.user:
        db.session.delete(clinic.user)
    
    db.session.delete(clinic)
    db.session.commit()
    flash("Clínica removida com sucesso!")
    return redirect(url_for("clinics.list_clinics"))