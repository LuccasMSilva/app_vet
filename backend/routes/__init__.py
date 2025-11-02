from flask import Blueprint
from .auth import auth_bp
from .dashboard import dashboard_bp
from .animals import animals_bp
from .clinics import clinics_bp

def register_blueprints(app):
    """Registra todos os blueprints da aplicação"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(animals_bp)
    app.register_blueprint(clinics_bp)