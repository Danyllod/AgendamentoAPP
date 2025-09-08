from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instância única do SQLAlchemy para ser utilizada em toda a aplicação.
db = SQLAlchemy()

# Configuração e instância única do LoginManager.
login_manager = LoginManager()
login_manager.login_view = 'login'  # Define a rota padrão para redirecionamento de login.
login_manager.session_protection = 'strong'
