from flask import Blueprint

journal_bp = Blueprint('journal', __name__,
                      template_folder='templates',
                      static_folder='static')

from app.blueprints.journal import routes