import os
import sys
from datetime import datetime

# Add project root to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from database.models import Users, UserIntegrations

# Load environment variables
load_dotenv()

def add_oura_integration(username, api_key):
    """Add or update Oura Ring integration for a user."""
    try:
        # Find the user
        user = Users.query.filter_by(username=username).first()
        if not user:
            print(f"User {username} not found")
            return False
            
        # Check if integration already exists
        integration = UserIntegrations.query.filter_by(
            user_id=user.user_id,
            integration_type='oura'
        ).first()
        
        if integration:
            # Update existing integration
            integration.set_credentials({'api_key': api_key})
            integration.status = 'active'
            integration.updated_at = datetime.utcnow()
            print(f"Updated Oura integration for user {username}")
        else:
            # Create new integration
            integration = UserIntegrations(
                user_id=user.user_id,
                integration_type='oura',
                credentials={'api_key': api_key}
            )
            db.session.add(integration)
            print(f"Added new Oura integration for user {username}")
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Main function that can be run either via terminal or as a script."""
    app = create_app()
    
    with app.app_context():
        if len(sys.argv) == 3:
            # Command line usage
            username = sys.argv[1]
            api_key = sys.argv[2]
        else:
            # Interactive usage
            username = input("Enter username: ")
            api_key = input("Enter Oura API key: ")
        
        success = add_oura_integration(username, api_key)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()