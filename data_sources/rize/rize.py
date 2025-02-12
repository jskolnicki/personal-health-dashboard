import os
import sys
from datetime import datetime, date, timedelta
import pandas as pd
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

# Add project root to Python path
sys.path.append(PROJECT_ROOT)

# Load environment variables
load_dotenv()

from utils.logging_config import setup_logging
from database.models import RizeSession, RizeSummary
from data_sources.rize.api import RizeAPI

logger = setup_logging()

def process_session_record(record: Dict) -> Dict:
    """
    Process a single session record from the Rize API.
    All times are converted to UTC.
    """
    # Convert to UTC datetime objects
    start_time = pd.to_datetime(record['startTime']).tz_convert('UTC')
    end_time = pd.to_datetime(record['endTime']).tz_convert('UTC')
    created_at = pd.to_datetime(record['createdAt'])  # Already in UTC based on 'Z' suffix
    
    return {
        'session_id': record['id'],
        'title': record['title'],
        'description': record['description'],
        'type': record['type'],
        'source': record['source'],
        'start_time': start_time,
        'end_time': end_time,
        'date': start_time.date(),  # Using UTC date from start_time
        'duration_minutes': int((end_time - start_time).total_seconds() / 60),
        'created_at': created_at
    }

def process_summary_record(record: Dict) -> Dict:
    """
    Process a single summary record from the Rize API bucket data.
    The date represents a local day boundary (4am to 4am).
    """
    local_date = record['date'].split()[0] # Extract just the date portion from the string (before the time)
    date_obj = datetime.strptime(local_date, '%Y-%m-%d').date()
    
    return {
        'date': date_obj,
        'wday': record['wday'],
        'focus_time': int(record['focusTime']),
        'break_time': int(record['breakTime']),
        'meeting_time': int(record['meetingTime']),
        'tracked_time': int(record['trackedTime']),
        'work_hours': int(record['workHours']),
        'daily_meeting_time_average': int(record['dailyMeetingTimeAverage']),
        'daily_tracked_time_average': int(record['dailyTrackedTimeAverage']),
        'daily_focus_time_average': int(record['dailyFocusTimeAverage']),
        'daily_work_hours_average': int(record['dailyWorkHoursAverage'])
    }

def update_rize_sessions(db_manager, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Update just the Rize session data"""
    if not (start_date and end_date):
        start_date, end_date = db_manager.get_update_date_range(RizeSession, date_column='date')
    
    logger.debug(f"Fetching Rize sessions for period {start_date} to {end_date}")
    
    rize_api = RizeAPI(os.getenv('RIZE_API_KEY'))
    
    # Request a wider time range from the API to ensure we catch all sessions
    # that might appear in different timezones
    start_datetime = datetime.combine(start_date, datetime.min.time()) - timedelta(days=1)
    end_datetime = datetime.combine(end_date, datetime.max.time()) + timedelta(days=1)
    
    sessions_data = rize_api.get_sessions(start_datetime, end_datetime)
    
    processed_sessions = []
    session_ids = set()  # All session IDs from API, regardless of date
    
    for record in sessions_data:
        try:
            processed_record = process_session_record(record)
            # Collect ALL session IDs from the API response
            session_ids.add(processed_record['session_id'])
            
            # Only add to processed_sessions if it falls within our target date range
            session_date = processed_record['date']
            if start_date <= session_date <= end_date:
                processed_sessions.append(processed_record)
        except Exception as e:
            logger.error(f"Error processing session record: {str(e)}")
            continue
    
    # Enhanced deletion logging with safeguards
    if session_ids:  # Only proceed if we got data from the API
        session = db_manager.Session()
        try:
            # Only get existing sessions from our exact target date range
            existing_ids = db_manager.get_existing_session_ids(start_date, end_date)
            # A session should only be deleted if it exists in our DB but is not found
            # anywhere in the expanded API response
            ids_to_delete = existing_ids - session_ids
            
            if ids_to_delete:
                to_delete = session.query(RizeSession)\
                    .filter(RizeSession.session_id.in_(ids_to_delete))\
                    .filter(RizeSession.date >= start_date)\
                    .filter(RizeSession.date <= end_date)\
                    .all()
                
                if to_delete:
                    logger.info(f"Found sessions to delete within date range {start_date} to {end_date}:")
                    for session_to_delete in to_delete:
                        logger.info(f"Deleting session: {session_to_delete.session_id} "
                                  f"from {session_to_delete.date} "
                                  f"(start: {session_to_delete.start_time}, "
                                  f"end: {session_to_delete.end_time})")
                    
                    session.query(RizeSession)\
                        .filter(RizeSession.session_id.in_(ids_to_delete))\
                        .filter(RizeSession.date >= start_date)\
                        .filter(RizeSession.date <= end_date)\
                        .delete(synchronize_session=False)
                    session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error managing sessions: {str(e)}")
            raise
        finally:
            session.close()
    
    if processed_sessions:
        db_manager.upsert_rize_sessions(processed_sessions)
        
    return len(processed_sessions)

def update_rize_summaries(db_manager, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Update just the Rize summary data"""
    if not (start_date and end_date):
        start_date, end_date = db_manager.get_update_date_range(RizeSummary, date_column='date')

    start_date = start_date - timedelta(days=1) # rize data can update as the day goes on
    
    logger.debug(f"Fetching Rize summaries for period {start_date} to {end_date}")
    
    rize_api = RizeAPI(os.getenv('RIZE_API_KEY'))
    summary_data = rize_api.get_summaries(start_date, end_date)
    
    summary_records = []
    if summary_data and 'buckets' in summary_data:
        for bucket in summary_data['buckets']:
            try:
                summary_record = process_summary_record(bucket)
                summary_records.append(summary_record)
            except Exception as e:
                logger.error(f"Error processing summary bucket for date {bucket.get('date', 'unknown')}: {str(e)}")
                continue
    
    if summary_records:
        db_manager.upsert_rize_summaries(summary_records)
        
    return len(summary_records)

def update_rize_data(db_manager, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Main update function that calls both session and summary updates"""
    try:
        sessions_count = update_rize_sessions(db_manager, start_date, end_date)
        summaries_count = update_rize_summaries(db_manager, start_date, end_date)
        
        logger.info(f"Rize data update completed successfully: "
                   f"{sessions_count} sessions, {summaries_count} daily summaries")
    except Exception as e:
        logger.error(f"Error updating Rize data: {str(e)}")
        raise

if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from database.models import get_database_engine
    
    engine = get_database_engine()
    db_manager = DatabaseManager(engine)
    
    # Setting start_date and end_date to None updates from the last updated date in the database
    start_date = None
    end_date = None
    
    start_date = date(2025, 1, 29)  # for custom date range
    end_date = date(2025, 1, 29)  # for custom date range
    
    try:
        update_rize_data(db_manager, start_date, end_date)
        print("Rize data update completed successfully.")
    except Exception as e:
        print(f"Failed to update Rize data: {e}")
        sys.exit(1)