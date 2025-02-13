import os
import sys
from datetime import datetime, date
import pandas as pd
from typing import List, Dict
from dotenv import load_dotenv
from sqlalchemy import func

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '../../..'))
sys.path.append(PROJECT_ROOT)

# Load environment variables
load_dotenv()

from app.extensions import db
from app import create_app
from database.models import Vitals
from etl.data_sources.google_sheets.api import GoogleSheetsAPI
from utils.date_utils import get_date_range
from utils.logging_config import setup_logging

logger = setup_logging()

SPREADSHEET_ID = os.getenv('VITALS_SHEET_ID')
SHEET_NAME = "Vitals"
RANGE_NAME = f"'{SHEET_NAME}'!A:J"  # Adjust range based on your columns

# Add this import at the top with other imports
from utils.date_utils import get_date_range

def process_vitals_record(record: Dict) -> Dict:
    """
    Process a single vitals record from the raw data.
    Returns None if all value columns are empty.
    """
    # Convert date string to date object
    record_date = pd.to_datetime(record['Date']).date()
    
    # Process wake up time
    wake_up_time = None
    if pd.notna(record['Wake Up']) and record['Wake Up'].strip():
        time_str = record['Wake Up'].strip()
        try:
            time_obj = datetime.strptime(time_str, '%I:%M:%S %p')
            wake_up_time = datetime.combine(record_date, time_obj.time())
        except ValueError:
            logger.warning(f"Invalid wake up time format for date {record_date}: {time_str}")
            wake_up_time = None
    
    # Helper functions remain the same
    def parse_float(value):
        try:
            return float(value) if pd.notna(value) and str(value).strip() != '' else None
        except (ValueError, TypeError):
            return None
    
    def parse_int(value):
        try:
            return int(float(value)) if pd.notna(value) and str(value).strip() != '' else None
        except (ValueError, TypeError):
            return None
    
    processed = {
        'date': record_date,
        'wake_up_time': wake_up_time,
        'sleep_minutes': parse_int(record['Sleep Mins']),
        'weight': parse_float(record['Weight']),
        'nap_minutes': parse_int(record['Nap (today)']),
        'drinks': parse_int(record['Drinks'])
    }
    
    # Check if all value columns are None
    values = [v for k, v in processed.items() if k != 'date']
    if all(v is None for v in values):
        return None
    
    return processed

def process_vitals_data(raw_data: List[List], start_date, end_date) -> List[Dict]:
    """Process raw vitals data from Google Sheets into structured records."""
    if not raw_data:
        return []
    
    # Create DataFrame and convert dates in one step
    df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # Filter by date range
    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    
    # Process records
    processed_records = []
    for _, row in df.iterrows():
        try:
            processed_record = process_vitals_record(row.to_dict())
            if processed_record is not None:  # Only add if record has some data
                processed_records.append(processed_record)
        except Exception as e:
            logger.error(f"Error processing record {row}: {str(e)}")
            continue
    
    return processed_records

def update_vitals_data(start_date=None, end_date=None):
    """Update vitals data in the database."""
    try:
        if not (start_date and end_date):
            start_date, end_date = get_date_range(Vitals, 'date')
            
        logger.debug(f"Fetching vitals data for period {start_date} to {end_date}")
        
        api = GoogleSheetsAPI()
        raw_data = api.get_sheet_data(SPREADSHEET_ID, RANGE_NAME)
        
        if not raw_data:
            logger.warning("No vitals data available from Google Sheets.")
            return
        
        # Process the raw data
        processed_records = process_vitals_data(raw_data, start_date, end_date)
        
        logger.debug(f"Upserting {len(processed_records)} vitals records")
        
        # Upsert records
        try:
            for record in processed_records:
                existing = Vitals.query.filter_by(date=record['date']).first()
                if existing:
                    for key, value in record.items():
                        setattr(existing, key, value)
                else:
                    new_record = Vitals(**record)
                    db.session.add(new_record)
            
            db.session.commit()
            logger.info(f"Vitals data upserted: {len(processed_records)} records")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error upserting vitals records: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"An error occurred while processing vitals data: {str(e)}")
        raise

if __name__ == "__main__":
   app = create_app()
   
   with app.app_context():
       # Option 1: Use most recent data
       # start_date = None
       # end_date = None
       
       # Option 2: Use specific date range
       start_date = date(2025, 1, 1)
       end_date = date(2025, 12, 31)
       
       try:
           update_vitals_data(start_date, end_date)
           print("Vitals data update completed successfully.")
       except Exception as e:
           print(f"Failed to update vitals data: {e}")
           sys.exit(1)