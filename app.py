from flask import Flask
from extensions import db, login_manager
from dashboard import init_dashboard
from routes import load_routes
from flask_migrate import Migrate
from db import init_db



def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agendamento.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'Mcpjst22p'

    # Inicializa as extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    # Inicializa o dashboard (Dash integrado com Flask)
    init_dashboard(app)

    # Carrega as rotas
    with app.app_context():
        load_routes(app)
        db.create_all()  # Cria as tabelas caso não existam (ou utilize migrações)

    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    app.run(debug=True, host='192.168.3.98')

