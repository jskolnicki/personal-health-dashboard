import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

from app import create_app
from app.extensions import db

def create_database(app):
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    app = create_app()
    create_database(app)