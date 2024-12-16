from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
from database.models import RizeSession

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    from app.routes import dashboard
    app.register_blueprint(dashboard.bp)
    
    return app