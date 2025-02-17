import os
import sys
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '../../..'))
sys.path.append(PROJECT_ROOT)

from datetime import datetime, timedelta, date
from dateutil import parser
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from sqlalchemy import func
from flask import current_app

load_dotenv()

from app.extensions import db
from app import create_app
from database.models import SleepData, NapData, UserIntegrations
from etl.data_sources.oura.api import OuraAPI
from utils.date_utils import get_date_range
from utils.logging_config import setup_logging

logger = setup_logging()

def categorize_sleep_sessions(sleep_sessions: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """
    Categorizes sleep sessions into main sleep and naps.
    
    Args:
    sleep_sessions (List[Dict]): List of sleep sessions for a single day.
    
    Returns:
    Tuple[Dict, List[Dict]]: A tuple containing the main sleep session and a list of naps.
    """
    if len(sleep_sessions) == 1:
        return sleep_sessions[0], []
    
    main_sleep = None
    naps = []
    
    for session in sleep_sessions:
        sleep_start = datetime.fromisoformat(session['bedtime_start'])
        sleep_duration = session['total_sleep_duration'] / 3600  # Convert to hours
        
        # Check if the sleep session starts between 8 PM and 3 AM and is longer than 3 hours
        if (sleep_start.hour >= 20 or sleep_start.hour < 3) and sleep_duration > 3:
            if main_sleep is None or sleep_duration > main_sleep['total_sleep_duration'] / 3600:
                if main_sleep:
                    naps.append(main_sleep)
                main_sleep = session
        else:
            naps.append(session)
    
    # If no main sleep was found, use the first session as main sleep
    if main_sleep is None:
        main_sleep = sleep_sessions[0]
        naps = sleep_sessions[1:]
    
    return main_sleep, naps

def calculate_sleep_metrics(sleep_data: Dict) -> Dict:
    # This function remains unchanged as it doesn't involve database operations
    bedtime_start = parser.isoparse(sleep_data['bedtime_start'])
    bedtime_end = parser.isoparse(sleep_data['bedtime_end'])
    sleep_phases = sleep_data['sleep_phase_5_min']
    
    # Calculate sleep_start
    initial_awake = 0
    for phase in sleep_phases:
        if phase == '4':
            initial_awake += 1
        else:
            break
    sleep_start = bedtime_start + timedelta(minutes=initial_awake * 5)
    
    # Calculate sleep_end
    final_awake = 0
    for phase in reversed(sleep_phases):
        if phase == '4':
            final_awake += 1
        else:
            break
    sleep_end = bedtime_end - timedelta(minutes=final_awake * 5)
    
    # Calculate midsleep_awake_time
    midsleep_awake_time = 0
    awake_streak = 0
    for phase in sleep_phases[initial_awake:-final_awake or None]:
        if phase == '4':
            awake_streak += 1
        else:
            if awake_streak > 1:
                midsleep_awake_time += awake_streak * 5
            awake_streak = 0
    
    return {
        'sleep_start': sleep_start,
        'sleep_end': sleep_end,
        'midsleep_awake_time': midsleep_awake_time
    }

def process_sleep_session(session: Dict, user_id: int) -> Dict:
    def process_datetime(dt):
        offset = dt.utcoffset()
        offset_minutes = int(offset.total_seconds() / 60) if offset else 0
        return dt.replace(tzinfo=None), offset_minutes

    custom_metrics = calculate_sleep_metrics(session)
    
    bedtime_start, timezone_offset = process_datetime(parser.isoparse(session['bedtime_start']))
    bedtime_end, _ = process_datetime(parser.isoparse(session['bedtime_end']))
    sleep_start, _ = process_datetime(custom_metrics['sleep_start'])
    sleep_end, _ = process_datetime(custom_metrics['sleep_end'])

    processed_data = {
        'user_id': user_id,
        'date': session['day'],
        'bedtime_start': bedtime_start,
        'bedtime_end': bedtime_end,
        'sleep_start': sleep_start,
        'sleep_end': sleep_end,
        'timezone_offset': timezone_offset,
        'total_sleep_duration': session['total_sleep_duration'],
        'time_in_bed': session['time_in_bed'],
        'sleep_awake_time': session['awake_time'],
        'midsleep_awake_time': custom_metrics['midsleep_awake_time'],
        'deep_sleep_duration': session.get('deep_sleep_duration', 0),
        'light_sleep_duration': session.get('light_sleep_duration', 0),
        'rem_sleep_duration': session.get('rem_sleep_duration', 0),
        'restless_periods': session.get('restless_periods', 0),
        'average_heart_rate': session.get('average_heart_rate'),
        'average_hrv': session.get('average_hrv'),
        'latency': session.get('latency')
    }

    return processed_data

def process_oura_data(oura_data: List[Dict], user_id: int) -> Tuple[List[Dict], List[Dict]]:
    sleep_data = []
    nap_data = []

    # Group sessions by day
    sessions_by_day = {}
    for session in oura_data:
        day = session['day']
        if day not in sessions_by_day:
            sessions_by_day[day] = []
        sessions_by_day[day].append(session)

    # Process each day
    for day, sessions in sessions_by_day.items():
        main_sleep, naps = categorize_sleep_sessions(sessions)
        
        sleep_data.append(process_sleep_session(main_sleep, user_id))
        
        for nap in naps:
            nap_data.append(process_sleep_session(nap, user_id))

    return sleep_data, nap_data

def update_oura_sleep_data(start_date=None, end_date=None):
    """
    Update Oura sleep data in the database for all users with active Oura integrations.
    If no date range is provided, it will determine the range based on each user's most recent record.
    """
    try:
        integrations = UserIntegrations.query\
            .filter_by(integration_type='oura', status='active')\
            .all()
        
        if not integrations:
            logger.info("No active Oura integrations found")
            return
        
        for integration in integrations:
            try:
                user = integration.user
                
                # Get user-specific date range if not provided
                user_start_date, user_end_date = start_date, end_date
                if not (user_start_date and user_end_date):
                    # Get date range from utility function
                    user_start_date, user_end_date = get_date_range(SleepData, 'date', user_id=user.user_id)
                    
                    # Always include the most recent day's data for potential updates
                    if user_start_date:
                        user_start_date = user_start_date - timedelta(days=1)
                
                # Get credentials and initialize API
                credentials = integration.get_credentials()
                oura_api = OuraAPI(access_token=credentials.get('api_key'))
                
                try:
                    # Fetch sleep data
                    raw_sleep_data = oura_api.get_sleep_data(user_start_date, user_end_date)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to process data for {user.username}: API error - {str(e)}")
                    integration.update_sync_status(success=False)
                    continue
                
                if not raw_sleep_data or 'data' not in raw_sleep_data:
                    logger.info(f"No new sleep data available for {user.username}")
                    integration.update_sync_status(success=True)
                    continue
                
                # Process the data
                processed_sleep_data, processed_nap_data = process_oura_data(raw_sleep_data['data'], user.user_id)
                
                # Upsert sleep data
                for sleep_record in processed_sleep_data:
                    if isinstance(sleep_record['date'], str):
                        sleep_record['date'] = date.fromisoformat(sleep_record['date'])
                    
                    existing = SleepData.query.filter_by(
                        user_id=sleep_record['user_id'],
                        date=sleep_record['date']
                    ).first()
                    
                    if existing:
                        for key, value in sleep_record.items():
                            setattr(existing, key, value)
                    else:
                        new_sleep = SleepData(**sleep_record)
                        db.session.add(new_sleep)
                
                # Upsert nap data
                for nap_record in processed_nap_data:
                    if isinstance(nap_record['date'], str):
                        nap_record['date'] = date.fromisoformat(nap_record['date'])
                    
                    existing = NapData.query.filter_by(
                        user_id=nap_record['user_id'],
                        date=nap_record['date'],
                        bedtime_start=nap_record['bedtime_start']
                    ).first()
                    
                    if existing:
                        for key, value in nap_record.items():
                            setattr(existing, key, value)
                    else:
                        new_nap = NapData(**nap_record)
                        db.session.add(new_nap)
                
                db.session.commit()
                integration.update_sync_status(success=True)
                logger.info(f"Successfully processed {len(processed_sleep_data)} sleep records and {len(processed_nap_data)} nap records for {user.username}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to process data for {user.username if 'user' in locals() else integration.user_id}: {str(e)}")
                integration.update_sync_status(success=False)
                continue
                
    except Exception as e:
        logger.error(f"An error occurred while processing Oura sleep data: {str(e)}")
        raise

if __name__ == "__main__":
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Option 1: Use most recent data
        start_date = None
        end_date = None
        
        # Option 2: Use specific date range
        # start_date = date(2024, 1, 1)
        # end_date = date(2024, 12, 31)
        
        try:
            update_oura_sleep_data(start_date, end_date)
            print("Oura sleep data update completed successfully.")
        except Exception as e:
            print(f"Failed to update Oura sleep data: {e}")
            exit(1)