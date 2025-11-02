from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from backend.extensions import db
from backend.models import Animal, User, Clinic
from sqlalchemy.orm import joinedload

animals_bp = Blueprint('animals', __name__)

@animals_bp.route("/animals")
def list_animals():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user = db.session.get(User, session["user_id"])
    if user.role == 'admin':
        animals = Animal.query.options(
            joinedload(Animal.dono),
            joinedload(Animal.clinic)
        ).all()
    elif user.role == 'clinic':
        clinic = Clinic.query.filter_by(user_id=user.id).first()
        animals = Animal.query.filter_by(clinic_id=clinic.id)\
            .options(joinedload(Animal.dono))\
            .all()
    else:
        animals = Animal.query.filter_by(dono_id=user.id)\
            .options(joinedload(Animal.clinic))\
            .all()
    
    return render_template("animals/list.html", animals=animals)

@animals_bp.route("/animals/add", methods=["GET", "POST"])
def add_animal():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        animal = Animal(
            nome=request.form["nome"],
            especie=request.form["especie"],
            raca=request.form["raca"],
            idade=request.form["idade"],
            dono_id=session["user_id"]
        )
        db.session.add(animal)
        db.session.commit()
        flash("Animal adicionado com sucesso!")
        return redirect(url_for("animals.list_animals"))
    
    return render_template("animals/add.html")

@animals_bp.route("/animals/<int:id>/edit", methods=["GET", "POST"])
def edit_animal(id):
    animal = Animal.query.get_or_404(id)
    
    if "user_id" not in session or \
       (session["role"] != "admin" and animal.dono_id != session["user_id"]):
        flash("Acesso negado", "error")
        return redirect(url_for("animals.list_animals"))
    
    if request.method == "POST":
        animal.nome = request.form["nome"]
        animal.especie = request.form["especie"]
        animal.raca = request.form["raca"]
        animal.idade = request.form["idade"]
        
        db.session.commit()
        flash("Animal atualizado com sucesso!")
        return redirect(url_for("animals.list_animals"))
    
    return render_template("animals/edit.html", animal=animal)

@animals_bp.route("/animals/<int:id>/delete", methods=["POST"])
def delete_animal(id):
    animal = Animal.query.get_or_404(id)
    
    if "user_id" not in session or \
       (session["role"] != "admin" and animal.dono_id != session["user_id"]):
        flash("Acesso negado", "error")
        return redirect(url_for("animals.list_animals"))
    
    db.session.delete(animal)
    db.session.commit()
    flash("Animal removido com sucesso!")
    return redirect(url_for("animals.list_animals"))