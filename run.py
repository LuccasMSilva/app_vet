from flask import Flask
from backend.extensions import db, login_manager
from backend.routes import register_blueprints
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    # Obter o diretório base do projeto
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Criar a aplicação Flask
    app = Flask(__name__,
                instance_path=os.path.join(basedir, 'instance'),
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # Configuração da aplicação
    app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-dificill'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'pets.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Configurar handler de erros
    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        from werkzeug.exceptions import NotFound
        
        # Log full traceback
        tb = traceback.format_exc()
        logger.error('Unhandled Exception:\n%s', tb)
        
        if isinstance(e, NotFound):
            return e
        
        if app.debug:
            raise e
        
        return '<h1>Erro interno</h1><p>Ocorreu um erro no servidor.</p>', 500
    
    return app

def init_db():
    """Inicializa o banco de dados e cria o usuário admin se necessário"""
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Adicionar dados iniciais (admin) se não existirem
        from backend.models import User
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()

if __name__ == "__main__":
    app = create_app()
    init_db()
    app.run(debug=True, host='0.0.0.0', use_reloader=False)