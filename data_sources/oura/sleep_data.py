import os
import sys
from datetime import datetime, timedelta, date
from dateutil import parser
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

# Add project root to Python path
sys.path.append(PROJECT_ROOT)

from database.models import SleepData

# Load environment variables from the project root's .env file
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from data_sources.oura.api import OuraAPI
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

def update_oura_sleep_data(db_manager, start_date, end_date):
    """
    Update Oura sleep data in the database.
    If no date range is provided, it will determine the range based on the most recent record.
    """
    try:
        if not (start_date and end_date):
            start_date, end_date = db_manager.get_update_date_range(SleepData)
            
        logger.debug(f"Updating Oura sleep data from {start_date} to {end_date}")

        user_id = 1  # TODO: Implement logic to retrieve the User ID

        logger.debug(f"Fetching sleep data for user {user_id} from {start_date} to {end_date}")
        
        oura_api = OuraAPI()
        raw_sleep_data = oura_api.get_sleep_data(start_date, end_date)
        
        if not raw_sleep_data or 'data' not in raw_sleep_data:
            logger.warning("No sleep data available or invalid response from Oura API.")
            return
        
        processed_sleep_data, processed_nap_data = process_oura_data(raw_sleep_data['data'], user_id)
        
        logger.debug(f"Inserting {len(processed_sleep_data)} sleep records and {len(processed_nap_data)} nap records")
        
        db_manager.upsert_sleep_data(processed_sleep_data)
        db_manager.upsert_nap_data(processed_nap_data)
        
        logger.info(f"Oura data upserted: {len(processed_sleep_data)} sleep records, {len(processed_nap_data)} nap records.")

    except Exception as e:
        logger.error(f"An error occurred while processing Oura sleep data: {str(e)}")
        raise

if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from database.models import get_database_engine
    
    engine = get_database_engine()
    db_manager = DatabaseManager(engine)

    # Setting start_date and end_date to None updates from the last updated date in the database
    start_date = None
    end_date = None

    # start_date = date(2024, 1, 1) # for custom date range
    # end_date = date(2024, 12, 31) # for custom date range
    
    try:
        update_oura_sleep_data(db_manager, start_date, end_date)
        print("Oura sleep data update completed successfully.")
    except Exception as e:
        print(f"Failed to update Oura sleep data: {e}")
        sys.exit(1)