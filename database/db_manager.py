import os
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
from dateutil import parser
from typing import Type, Tuple
from sqlalchemy.orm import Session

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

# Add project root to Python path
sys.path.append(PROJECT_ROOT)

from utils.logging_config import setup_logging
logger = setup_logging()

# Load environment variables from the project root's .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from database.models import SleepData, NapData


###############################################################################################
# Functions
def get_date_range_from_last_record(
    session: Session,
    table_class: Type,
    date_column: str = 'date'
) -> Tuple[date, date]:
    """
    Get the date range from the most recent record in the database to today.
    
    Args:
        session: SQLAlchemy session
        table_class: SQLAlchemy model class (e.g., SleepData, FinanceData)
        date_column: Name of the date column to query
    
    Returns:
        Tuple of (start_date, end_date) where:
        - start_date: Day after the most recent record (or Jan 1, 2019 if no records)
        - end_date: Tomorrow (to ensure we get today's data)
    """
    try:
        # Get the most recent date from the table
        date_col = getattr(table_class, date_column)
        last_record_date = session.query(func.max(date_col)).scalar()
        
        # Set end_date to tomorrow to ensure we get today's data
        end_date = date.today() + timedelta(days=1)
        
        if last_record_date:
            # Start from the day after the last record
            start_date = last_record_date + timedelta(days=1)
            
            # If we're already up to date, return None or same dates
            if start_date > end_date:
                return end_date, end_date
        else:
            # If no records exist, default to January 1, 2019
            start_date = date(2018, 1, 1)
        
        return start_date, end_date
        
    except Exception as e:
        logger.error(f"Error getting date range for {table_class.__name__}: {str(e)}")
        raise
###############################################################################################

class DatabaseManager:
    def __init__(self, engine):
        self.Session = sessionmaker(bind=engine)

    def get_update_date_range(self, table_class: Type, date_column: str = 'date') -> Tuple[date, date]:
        """Wrapper for getting date range that needs to be updated"""
        session = self.Session()
        try:
            return get_date_range_from_last_record(session, table_class, date_column)
        finally:
            session.close()

    def upsert_sleep_data(self, sleep_data):
        session = self.Session()
        try:
            for sleep in sleep_data:
                date = parser.isoparse(sleep['date']).date()
                existing = session.query(SleepData).filter_by(
                    user_id=sleep['user_id'],
                    date=date
                ).first()

                if existing:
                    for key, value in sleep.items():
                        setattr(existing, key, value)
                else:
                    new_sleep = SleepData(**sleep)
                    session.add(new_sleep)

            session.commit()
            print(f"Successfully upserted {len(sleep_data)} sleep records.")
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error upserting sleep data: {e}")
        finally:
            session.close()

    def upsert_nap_data(self, nap_data):
        session = self.Session()
        try:
            for nap in nap_data:
                date = parser.isoparse(nap['date']).date()
                existing = session.query(NapData).filter_by(
                    user_id=nap['user_id'],
                    date=date,
                    bedtime_start=nap['bedtime_start']
                ).first()

                if existing:
                    for key, value in nap.items():
                        setattr(existing, key, value)
                else:
                    new_nap = NapData(**nap)
                    session.add(new_nap)

            session.commit()
            print(f"Successfully upserted {len(nap_data)} nap records.")
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error upserting nap data: {e}")
        finally:
            session.close()