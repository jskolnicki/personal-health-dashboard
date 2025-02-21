from flask import Flask, request, redirect
from app.extensions import db
from config import Config

from flask_login import LoginManager
from database.models import Users

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # # Add before_request handler
    # @app.before_request
    # def force_https():
    #     if not request.is_secure and request.environ.get('HTTP_X_FORWARDED_PROTO', '') != 'https':
    #         url = request.url.replace('http://', 'https://', 1)
    #         return redirect(url)
    
    # Import and register blueprints
    from app.blueprints.home.routes import home_bp
    app.register_blueprint(home_bp)
    
    from app.blueprints.rize.routes import rize_bp
    app.register_blueprint(rize_bp)

    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.integrations.routes import integrations_bp
    app.register_blueprint(integrations_bp)
    
    from app.blueprints.journal.routes import journal_bp
    app.register_blueprint(journal_bp)
    
    return app