from flask import Flask
from config import Config
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.routes import auth, games, customers, loans
    app.register_blueprint(auth.bp)
    app.register_blueprint(games.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(loans.bp)

    # Register CLI commands
    from app.commands import init_db_command, create_admin_command
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)

    return app 