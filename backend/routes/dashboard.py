from flask import Blueprint, render_template, session, redirect, url_for
from sqlalchemy.orm import joinedload
from backend.extensions import db
from backend.models import User, Animal, Clinic

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user = db.session.get(User, session["user_id"])
    if not user:
        session.pop('user_id', None)
        session.pop("role", None)
        return redirect(url_for('auth.login'))

    # === VISÃO DO ADMIN ===
    if user.role == 'admin':
        all_animals = Animal.query.options(
            joinedload(Animal.dono), 
            joinedload(Animal.clinic)
        ).order_by(Animal.id.desc()).all()
        
        # Dados para os gráficos
        procedimentos = [animal.procedimento.lower() for animal in all_animals if animal.procedimento]
        procedimento_counts = {
            'castração': procedimentos.count('castração'),
            'consulta': procedimentos.count('consulta'),
            'vacina': procedimentos.count('vacina'),
            'cirurgia': procedimentos.count('cirurgia')
        }
        
        return render_template(
            "dashboard/admin.html",
            user=user,
            animals=all_animals,
            procedimento_counts=procedimento_counts
        )

    # === VISÃO DA CLÍNICA ===
    elif user.role == 'clinic':
        clinic = Clinic.query.filter_by(user_id=user.id).first()
        if not clinic:
            return render_template("error.html", message="Clínica não encontrada")
        
        clinic_animals = Animal.query.filter_by(clinic_id=clinic.id)\
            .options(joinedload(Animal.dono))\
            .order_by(Animal.id.desc())\
            .all()
            
        return render_template(
            "dashboard/clinic.html",
            user=user,
            clinic=clinic,
            animals=clinic_animals
        )

    # === VISÃO DO DONO DE PET ===
    else:
        user_animals = Animal.query.filter_by(dono_id=user.id)\
            .options(joinedload(Animal.clinic))\
            .order_by(Animal.id.desc())\
            .all()
            
        return render_template(
            "dashboard/user.html",
            user=user,
            animals=user_animals
        )