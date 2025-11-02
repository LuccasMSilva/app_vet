from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Extensões compartilhadas
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
