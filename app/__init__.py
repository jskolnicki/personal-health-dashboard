from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
from database.models import RizeSession

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Register blueprints
    from app.blueprints.rize.routes import rize_bp
    app.register_blueprint(rize_bp)
    
    # Register home blueprint
    from app.blueprints.home.routes import home_bp
    app.register_blueprint(home_bp)
    
    return app