import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

from app import create_app
from app.extensions import db
from database.models import Users
from getpass import getpass

app = create_app()

with app.app_context():
    user = Users.query.get(1)
    
    # getpass masks the input with asterisks
    new_password = getpass("Enter your new password: ")
    confirm_password = getpass("Confirm password: ")
    
    if new_password != confirm_password:
        print("Passwords don't match!")
        exit(1)
        
    user.set_password(new_password)
    db.session.commit()
    print("Password successfully set!")