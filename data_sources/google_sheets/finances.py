import os
import sys
from datetime import datetime, date
import pandas as pd
import hashlib
from typing import List, Dict
from dotenv import load_dotenv


# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

# Add project root to Python path
sys.path.append(PROJECT_ROOT)

# Load environment variables
load_dotenv()

from utils.logging_config import setup_logging
from data_sources.google_sheets.api import GoogleSheetsAPI
from database.models import FinanceData

logger = setup_logging()

SPREADSHEET_ID = os.getenv('FINANCES_SHEET_ID')
SHEET_NAME = "Transactions"
RANGE_NAME = f"'{SHEET_NAME}'!A:N"  # Adjust range based on your columns



###############################################################################
# Option 1: Dynamic dates
end_date = datetime.now().date()
start_date = (end_date.replace(day=1) - pd.DateOffset(months=1)).date()

# # Option 2: Specific dates
# start_date = datetime(2024, 3, 29).date()
# end_date = datetime(2024, 3, 29).date()

###############################################################################

def generate_transaction_hash(record: Dict) -> str:
    """
    Generate a unique hash for a transaction based on date, description, and amount.
    """
    hash_string = f"{record['transaction_date']}{record['description']}{record['amount']}"
    return hashlib.md5(hash_string.encode()).hexdigest()

def process_finance_record(record: Dict) -> Dict:
    """
    Process a single finance record from the raw data.
    """
    # Convert date string to date object
    transaction_date = pd.to_datetime(record['Date']).date()
    
    # Handle optional text fields
    category = record['Category'].strip() if record['Category'] is not None else None
    gift_type = record['Gift Type'].strip().lower() if record['Gift Type'] is not None else None
    person = record['Person'].strip() if record['Person'] is not None else None
    notes = record['Notes'].strip() if record['Notes'] is not None else None
    account_name = record['Account Name'].strip() if record['Account Name'] is not None else None
    transaction_type = record['Transaction Type'].strip().lower() if record['Transaction Type'] is not None else None
    
    # Handle boolean flags
    def parse_boolean(value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            value = value.strip().lower()
            return value in ('1', 'true', 'yes', 't', 'y')
        return False
    
    processed = {
        'transaction_date': transaction_date,
        'description': record['Description'].strip(),
        'amount': float(record['Amount']),
        'category': category,
        'transaction_type': transaction_type,
        'gift_type': gift_type,
        'person': person,
        'notes': notes,
        'account_name': account_name,
        'is_date': parse_boolean(record.get('date')),
        'is_vacation': parse_boolean(record.get('vacation')),
        'is_birthday': parse_boolean(record.get('birthday')),
        'is_christmas': parse_boolean(record.get('christmas'))
    }
    
    processed['transaction_hash'] = generate_transaction_hash(processed)
    
    return processed

def process_finance_data(raw_data: List[List], start_date, end_date) -> List[Dict]:
    """
    Process raw finance data from Google Sheets into structured records.
    """
    if not raw_data:
        return []
    
    # Create DataFrame from raw data
    df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
    
    # Convert dates and filter by date range first
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    
    # Then clean the filtered data
    df = df.dropna(how='all').reset_index(drop=True)
    df = df[df.astype(str).apply(lambda x: x.str.strip().str.len() > 0).any(axis=1)]
    df = df[df['Amount'].str.strip() != '']
    
    # Process records
    processed_records = []
    for _, row in df.iterrows():
        try:
            processed_record = process_finance_record(row.to_dict())
            processed_records.append(processed_record)
        except Exception as e:
            logger.error(f"Error processing record {row}: {str(e)}")
            continue
    
    return processed_records

def update_finance_data(db_manager, start_date=None, end_date=None):
    """
    Update finance data in the database.
    If no date range is provided, it will determine the range based on the most recent record.
    """
    try:
        if not (start_date and end_date):
            start_date, end_date = db_manager.get_update_date_range(FinanceData, date_column='transaction_date')
            
        logger.debug(f"Fetching finance data for period {start_date} to {end_date}")
        
        api = GoogleSheetsAPI()
        raw_data = api.get_sheet_data(SPREADSHEET_ID, RANGE_NAME)
        
        if not raw_data:
            logger.warning("No finance data available from Google Sheets.")
            return
        
        # Process the raw data
        processed_records = process_finance_data(raw_data, start_date, end_date)
        
        logger.debug(f"Upserting {len(processed_records)} finance records")
        
        # Get existing hashes for this date range
        existing_hashes = db_manager.get_existing_hashes(start_date, end_date)
        processed_hashes = set()
        
        # Upsert records using DatabaseManager's upsert method
        finance_records = []
        for record in processed_records:
            try:
                finance_records.append(record)
                processed_hashes.add(record['transaction_hash'])
            except Exception as e:
                logger.error(f"Error processing record {record}: {str(e)}")
                continue
        
        # Batch upsert all records
        if finance_records:
            try:
                db_manager.upsert_finance_data(finance_records)
            except Exception as e:
                logger.error(f"Error upserting finance records: {str(e)}")
                raise
        
        # Delete records that no longer exist in the spreadsheet
        hashes_to_delete = existing_hashes - processed_hashes
        if hashes_to_delete:
            logger.info(f"Deleting {len(hashes_to_delete)} removed records")
            session = db_manager.Session()
            try:
                session.query(FinanceData)\
                    .filter(
                        FinanceData.transaction_hash.in_(hashes_to_delete),
                        FinanceData.transaction_date.between(start_date, end_date)
                    ).delete(synchronize_session=False)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error deleting records: {str(e)}")
                raise
            finally:
                session.close()
        
        logger.info(f"Finance data upserted: {len(processed_records)} records")

    except Exception as e:
        logger.error(f"An error occurred while processing finance data: {str(e)}")
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
        update_finance_data(db_manager, start_date, end_date)
        print("Finance data update completed successfully.")
    except Exception as e:
        print(f"Failed to update finance data: {e}")
        sys.exit(1)