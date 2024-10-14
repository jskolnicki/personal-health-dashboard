import sys
import os
from datetime import date, timedelta, datetime
from typing import List, Dict, Tuple

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from data_sources.oura.api import OuraAPI
from database.db_manager import DatabaseManager
from database.models import create_database

#TODO preserve the time zones for this https://claude.ai/chat/e3decb0b-02df-4f34-9260-a4b74279cd61

def get_sleep_data(start_date: date = date.today() - timedelta(days=7), 
                   end_date: date = date.today()) -> List[Dict]:
    """
    Retrieves sleep data for the specified date range using the Oura API.
    
    Args:
    start_date (date): The start date for fetching sleep data.
    end_date (date): The end date for fetching sleep data.
    
    Returns:
    List[Dict]: A list of sleep data entries for the specified date range.
    """
    oura_api = OuraAPI()
    
    try:
        response = oura_api.get_sleep_data(start_date, end_date)
        return response['data']
    except Exception as e:
        print(f"Error fetching sleep data: {str(e)}")
        return []

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
    """
    Calculates custom sleep metrics based on the sleep phase data.
    
    Args:
    sleep_data (Dict): Raw sleep data for a single sleep session.
    
    Returns:
    Dict: Dictionary containing calculated sleep metrics.
    """
    bedtime_start = datetime.fromisoformat(sleep_data['bedtime_start'])
    bedtime_end = datetime.fromisoformat(sleep_data['bedtime_end'])
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
    
    # Calculate sleep_awake_time
    sleep_awake_time = 0
    awake_streak = 0
    for phase in sleep_phases[initial_awake:-final_awake or None]:
        if phase == '4':
            awake_streak += 1
        else:
            if awake_streak > 1:
                sleep_awake_time += awake_streak * 5
            awake_streak = 0
    
    return {
        'sleep_start': sleep_start,
        'sleep_end': sleep_end,
        'sleep_awake_time': sleep_awake_time
    }

def process_sleep_data(raw_sleep_data, user_id=1):
    processed_sleep = []
    processed_naps = []

    # Group sleep sessions by date
    sleep_by_date = {}
    for sleep in raw_sleep_data:
        date = sleep['day']
        if date not in sleep_by_date:
            sleep_by_date[date] = []
        sleep_by_date[date].append(sleep)

    for date, sessions in sleep_by_date.items():
        main_sleep, naps = categorize_sleep_sessions(sessions)

        # Process main sleep
        if main_sleep:
            processed = process_single_sleep_session(main_sleep, user_id)
            processed_sleep.append(processed)

        # Process naps
        for nap in naps:
            processed = process_single_sleep_session(nap, user_id)
            processed_naps.append(processed)

    return processed_sleep, processed_naps

def process_single_sleep_session(sleep, user_id):
    custom_metrics = calculate_sleep_metrics(sleep)
    
    return {
        'user_id': user_id,
        'date': sleep['day'],
        'bedtime_start': sleep['bedtime_start'],
        'bedtime_end': sleep['bedtime_end'],
        'sleep_start': custom_metrics['sleep_start'],
        'sleep_end': custom_metrics['sleep_end'],
        'total_sleep_duration': sleep['total_sleep_duration'],
        'time_in_bed': sleep['time_in_bed'],
        'sleep_awake_time': custom_metrics['sleep_awake_time'],
        'deep_sleep_duration': sleep.get('deep_sleep_duration', 0),
        'light_sleep_duration': sleep.get('light_sleep_duration', 0),
        'rem_sleep_duration': sleep.get('rem_sleep_duration', 0),
        'restless_periods': sleep.get('restless_periods', 0),
        'average_heart_rate': sleep.get('average_heart_rate'),
        'average_hrv': sleep.get('average_hrv')
    }

# Example usage
if __name__ == "__main__":
    engine = create_database()
    db_manager = DatabaseManager(engine)

    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    raw_sleep_data = get_sleep_data(start_date, end_date)
    
    if not raw_sleep_data:
        print("No sleep data available.")
    else:
        processed_sleep, processed_naps = process_sleep_data(raw_sleep_data)
        db_manager.upsert_sleep_data(processed_sleep)
        db_manager.upsert_nap_data(processed_naps)