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
    """
    start_time = pd.to_datetime(record['startTime'])
    end_time = pd.to_datetime(record['endTime'])
    
    return {
        'session_id': record['id'],
        'title': record['title'],
        'description': record['description'],
        'type': record['type'],
        'source': record['source'],
        'start_time': start_time,
        'end_time': end_time,
        'date': start_time.date(),
        'duration_minutes': int((end_time - start_time).total_seconds() / 60),
        'created_at': pd.to_datetime(record['createdAt'])
    }

def process_summary_record(record: Dict) -> Dict:
    """
    Process a single summary record from the Rize API bucket data.
    """
    return {
        'date': datetime.strptime(record['date'], '%Y-%m-%d').date(),
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

    start_date = start_date - timedelta(days=1) # rize data can update as the day goes on
    
    logger.debug(f"Fetching Rize sessions for period {start_date} to {end_date}")
    
    rize_api = RizeAPI(os.getenv('RIZE_API_KEY'))
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    sessions_data = rize_api.get_sessions(start_datetime, end_datetime)
    
    processed_sessions = []
    session_ids = set()
    
    for record in sessions_data:
        try:
            processed_record = process_session_record(record)
            processed_sessions.append(processed_record)
            session_ids.add(processed_record['session_id'])
        except Exception as e:
            logger.error(f"Error processing session record: {str(e)}")
            continue
    
    # Enhanced deletion logging
    if session_ids:
        session = db_manager.Session()
        try:
            existing_ids = db_manager.get_existing_session_ids(start_date, end_date)
            ids_to_delete = existing_ids - session_ids
            
            if ids_to_delete:
                logger.info(f"Found sessions to delete: {ids_to_delete}")
                # Get details of sessions being deleted for debugging
                to_delete = session.query(RizeSession)\
                    .filter(RizeSession.session_id.in_(ids_to_delete))\
                    .all()
                for session_to_delete in to_delete:
                    logger.info(f"Deleting session: {session_to_delete.session_id} "
                              f"from {session_to_delete.date}")
                
                session.query(RizeSession)\
                    .filter(RizeSession.session_id.in_(ids_to_delete))\
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
    
    # start_date = date(2024, 12, 10)  # for custom date range
    # end_date = date(2024, 12, 15)  # for custom date range
    
    try:
        update_rize_summaries(db_manager, start_date, end_date)
        update_rize_data(db_manager, start_date, end_date)
        print("Rize data update completed successfully.")
    except Exception as e:
        print(f"Failed to update Rize data: {e}")
        sys.exit(1)