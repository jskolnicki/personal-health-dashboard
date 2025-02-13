from flask import Flask
from app.extensions import db
from config import Config

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Initialize extensions
    db.init_app(app)
    
    # Import and register blueprints
    from app.blueprints.home.routes import home_bp
    app.register_blueprint(home_bp)
    
    from app.blueprints.rize.routes import rize_bp
    app.register_blueprint(rize_bp)
    
    # from app.blueprints.journal.routes import journal_bp
    # app.register_blueprint(journal_bp)
    
    return app