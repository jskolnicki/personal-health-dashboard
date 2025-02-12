"""
This file contains Flask extensions instances that are shared across the application.

Why this file exists:
1. Prevents circular imports - By having database (db) instances in a separate file,
   we avoid circular dependencies between models.py and app/__init__.py
2. Central location - Provides a single source of truth for all Flask extensions
3. Clean initialization - Extensions are created here without initialization, then 
   initialized with the app in create_app()

Example of the circular import issue this solves:
- app/__init__.py needs to import models to register them
- models.py needs to import db from app
- This would create a circular import without this extensions.py file

Pattern source: Flask documentation's recommendations for larger applications and 
the Flask application factory pattern.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()