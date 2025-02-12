import os
import sys

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

# Add project root to Python path
sys.path.append(PROJECT_ROOT)

from datetime import datetime, date, timedelta
import pandas as pd
from typing import List, Dict, Optional
from dotenv import load_dotenv
from sqlalchemy import func

# Load environment variables
load_dotenv()

from app.extensions import db
from app import create_app
from database.models import RizeSession, RizeSummary
from data_sources.rize.api import RizeAPI
from utils.date_utils import get_date_range
from utils.logging_config import setup_logging

logger = setup_logging()

def process_session_record(record: Dict) -> Dict:
    """Process functions remain unchanged as they don't involve database operations"""
    start_time = pd.to_datetime(record['startTime']).tz_convert('UTC')
    end_time = pd.to_datetime(record['endTime']).tz_convert('UTC')
    created_at = pd.to_datetime(record['createdAt'])
    
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
        'created_at': created_at
    }

def process_summary_record(record: Dict) -> Dict:
    """Process functions remain unchanged as they don't involve database operations"""
    local_date = record['date'].split()[0]
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

def get_existing_session_ids(start_date: date, end_date: date) -> set:
    """Get set of session IDs for a date range"""
    result = RizeSession.query\
        .filter(RizeSession.date.between(start_date, end_date))\
        .with_entities(RizeSession.session_id)\
        .all()
    return set(row[0] for row in result)

def update_rize_sessions(start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Update just the Rize session data"""
    if not (start_date and end_date):
        start_date, end_date = get_date_range(RizeSession, 'date')
    
    logger.debug(f"Fetching Rize sessions for period {start_date} to {end_date}")
    
    rize_api = RizeAPI(os.getenv('RIZE_API_KEY'))
    
    start_datetime = datetime.combine(start_date, datetime.min.time()) - timedelta(days=1)
    end_datetime = datetime.combine(end_date, datetime.max.time()) + timedelta(days=1)
    
    sessions_data = rize_api.get_sessions(start_datetime, end_datetime)
    
    processed_sessions = []
    session_ids = set()
    
    for record in sessions_data:
        try:
            processed_record = process_session_record(record)
            session_ids.add(processed_record['session_id'])
            
            session_date = processed_record['date']
            if start_date <= session_date <= end_date:
                processed_sessions.append(processed_record)
        except Exception as e:
            logger.error(f"Error processing session record: {str(e)}")
            continue
    
    if session_ids:
        try:
            existing_ids = get_existing_session_ids(start_date, end_date)
            ids_to_delete = existing_ids - session_ids
            
            if ids_to_delete:
                to_delete = RizeSession.query\
                    .filter(RizeSession.session_id.in_(ids_to_delete))\
                    .filter(RizeSession.date.between(start_date, end_date))\
                    .all()
                
                if to_delete:
                    logger.info(f"Found sessions to delete within date range {start_date} to {end_date}:")
                    for session_to_delete in to_delete:
                        logger.info(f"Deleting session: {session_to_delete.session_id} "
                                  f"from {session_to_delete.date} "
                                  f"(start: {session_to_delete.start_time}, "
                                  f"end: {session_to_delete.end_time})")
                    
                    RizeSession.query\
                        .filter(RizeSession.session_id.in_(ids_to_delete))\
                        .filter(RizeSession.date.between(start_date, end_date))\
                        .delete(synchronize_session=False)
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error managing sessions: {str(e)}")
            raise
    
    if processed_sessions:
        try:
            for session in processed_sessions:
                existing = RizeSession.query.filter_by(session_id=session['session_id']).first()
                if existing:
                    for key, value in session.items():
                        if key != 'created_at':
                            setattr(existing, key, value)
                else:
                    new_session = RizeSession(**session)
                    db.session.add(new_session)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error upserting sessions: {str(e)}")
            raise
        
    return len(processed_sessions)

def update_rize_summaries(start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Update just the Rize summary data"""
    if not (start_date and end_date):
        start_date, end_date = get_date_range(RizeSummary, 'date')
        
    start_date = start_date - timedelta(days=1)  # rize data can update as the day goes on
    
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
        try:
            for summary in summary_records:
                existing = RizeSummary.query.filter_by(date=summary['date']).first()
                if existing:
                    for key, value in summary.items():
                        setattr(existing, key, value)
                else:
                    new_summary = RizeSummary(**summary)
                    db.session.add(new_summary)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error upserting summaries: {str(e)}")
            raise
        
    return len(summary_records)

def update_rize_data(start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Main update function that calls both session and summary updates"""
    try:
        sessions_count = update_rize_sessions(start_date, end_date)
        summaries_count = update_rize_summaries(start_date, end_date)
        
        logger.info(f"Rize data update completed successfully: "
                   f"{sessions_count} sessions, {summaries_count} daily summaries")
    except Exception as e:
        logger.error(f"Error updating Rize data: {str(e)}")
        raise

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        # Option 1: Use most recent data
        # start_date = None
        # end_date = None
        
        # Option 2: Use specific date range
        start_date = date(2025, 1, 29)
        end_date = date(2025, 1, 29)
        
        try:
            update_rize_data(start_date, end_date)
            print("Rize data update completed successfully.")
        except Exception as e:
            print(f"Failed to update Rize data: {e}")
            sys.exit(1)