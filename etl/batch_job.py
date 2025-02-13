import os
import sys
from datetime import date, timedelta
from typing import Optional, Dict, Tuple, Callable
from dotenv import load_dotenv

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

load_dotenv()

from app import create_app
from etl.data_sources.oura.sleep_data import update_oura_sleep_data
from etl.data_sources.rize.rize import update_rize_data
from etl.data_sources.google_sheets.finances import update_finance_data
from etl.data_sources.google_sheets.vitals import update_vitals_data
from database.models import SleepData, RizeSummaries, RizeSessions, Finances, Vitals
from utils.logging_config import setup_logging
from utils.blinkstick import StatusManager

logger = setup_logging()

class DataSource:
    def __init__(
        self,
        name: str,
        update_func: Callable,
        model_class: type,
        date_column: str = 'date',
        custom_dates: Optional[Tuple[date, date]] = None
    ):
        self.name = name
        self.update_func = update_func
        self.model_class = model_class
        self.date_column = date_column
        self.custom_dates = custom_dates

def main(global_date_range: Optional[Tuple[date, date]] = None) -> bool:
    """
    Run data updates for all sources.
    
    Args:
        global_date_range: Optional tuple of (start_date, end_date) to apply to all sources
    
    Returns:
        bool: True if all updates succeeded, False if any failed
    """
    app = create_app()
    status_manager = StatusManager()  # Initialize once
    success = True

    # Define data sources with their configurations
    data_sources = [
        DataSource(
            name="Oura Sleep",
            update_func=update_oura_sleep_data,
            model_class=SleepData,
            date_column='date',
        ),
        DataSource(
            name="Rize Summaries and Sessions",
            update_func=update_rize_data,
            model_class=RizeSummaries,
            date_column='date',
        ),
        DataSource(
            name="Finances",
            update_func=update_finance_data,
            model_class=Finances,
            date_column='transaction_date',
        ),
        DataSource(
            name="Vitals",
            update_func=update_vitals_data,
            model_class=Vitals,
            date_column='date',
        )
    ]

    with app.app_context():
        for source in data_sources:
            try:
                status_manager.start_process(source.name)
                
                dates_to_use = source.custom_dates or global_date_range or (None, None)
                start_date, end_date = dates_to_use
                
                if start_date and end_date:
                    logger.debug(f"Processing {source.name} with custom date range: {start_date} to {end_date}")
                else:
                    logger.debug(f"Processing {source.name} using most recent data")
                
                source.update_func(start_date, end_date)
                status_manager.end_process(success=True)
                
            except Exception as e:
                success = False
                logger.error(f"Error occurred in {source.name} update: {str(e)}")
                status_manager.end_process(success=False)
                
    status_manager.cleanup()
    return success

if __name__ == "__main__":
    try:
        # Option 1: Use most recent data for all sources (default)
        start_date = None
        end_date = None

        # Option 2: Set global date range for all sources
        # start_date = date(2024, 1, 1)
        # end_date = date(2025, 1, 1)

        success = main((start_date, end_date))
        
        if success:
            print("All data updates completed successfully.")
        else:
            print("Some data updates failed. Check the logs for details.")
            sys.exit(1)
    except Exception as e:
        print(f"Failed to complete all data updates: {e}")
        sys.exit(1)