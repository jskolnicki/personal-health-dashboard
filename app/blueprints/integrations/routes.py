# app/blueprints/integrations/routes.py
from flask import Blueprint, render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from app.extensions import db
from database.models import UserIntegrations
import requests
from datetime import datetime
import os

integrations_bp = Blueprint('integrations', __name__, template_folder='templates')

OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/oauth/token"

# Make sure routes require login
@integrations_bp.route('/integrations')
@login_required
def index():
    """Only show integrations for logged-in users"""
    """Show available integrations and their status"""
    integrations = UserIntegrations.query.filter_by(user_id=current_user.user_id).all()
    oura_integration = next((i for i in integrations if i.integration_type == 'oura'), None)
    
    return render_template(
        'index.html',
        oura_integration=oura_integration
    )

@integrations_bp.route('/integrations/oura/connect')
@login_required
def connect_oura():
    """Initiate Oura OAuth flow"""
    client_id = os.getenv('OURA_CLIENT_ID')
    redirect_uri = url_for('integrations.oura_callback', _external=True)
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'state': 'your_state_here'  # In production, use a secure random state
    }
    
    auth_url = f"{OURA_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return redirect(auth_url)

@integrations_bp.route('/integrations/oura/callback')
@login_required
def oura_callback():
    """Handle Oura OAuth callback"""
    error = request.args.get('error')
    if error:
        flash(f'Error connecting to Oura: {error}', 'error')
        return redirect(url_for('integrations.index'))
    
    code = request.args.get('code')
    if not code:
        flash('No authorization code received from Oura', 'error')
        return redirect(url_for('integrations.index'))
    
    # Exchange code for token
    try:
        token_response = requests.post(OURA_TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': os.getenv('OURA_CLIENT_ID'),
            'client_secret': os.getenv('OURA_CLIENT_SECRET'),
            'redirect_uri': url_for('integrations.oura_callback', _external=True)
        })
        token_response.raise_for_status()
        token_data = token_response.json()
        
        # Store the access token
        integration = UserIntegrations.query.filter_by(
            user_id=current_user.user_id,
            integration_type='oura'
        ).first()
        
        if integration:
            integration.set_credentials({'api_key': token_data['access_token']})
            integration.status = 'active'
            integration.updated_at = datetime.utcnow()
        else:
            integration = UserIntegrations(
                user_id=current_user.user_id,
                integration_type='oura',
                credentials={'api_key': token_data['access_token']}
            )
            db.session.add(integration)
        
        db.session.commit()
        flash('Successfully connected to Oura Ring!', 'success')
        
    except requests.exceptions.RequestException as e:
        flash(f'Error exchanging code for token: {str(e)}', 'error')
    
    return redirect(url_for('integrations.index'))

@integrations_bp.route('/integrations/oura/disconnect', methods=['POST'])
@login_required
def disconnect_oura():
    """Remove Oura Ring integration"""
    integration = UserIntegrations.query.filter_by(
        user_id=current_user.user_id,
        integration_type='oura'
    ).first()
    
    if integration:
        db.session.delete(integration)
        db.session.commit()
        flash('Oura Ring integration has been removed', 'success')
    
    return redirect(url_for('integrations.index'))