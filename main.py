from datetime import date, timedelta
from typing import Optional, Dict, Tuple, Callable
from dotenv import load_dotenv

load_dotenv()

from data_sources.oura.sleep_data import update_oura_sleep_data
from data_sources.rize.rize import update_rize_data
from database.db_manager import DatabaseManager
from database.models import get_database_engine, SleepData, RizeSummary, RizeSession
from utils.logging_config import setup_logging
from utils.blinkstick import indicate_status, turn_off, set_color

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

def main(global_date_range: Optional[Tuple[date, date]] = None):
    """
    Run data updates for all sources.
    
    Args:
        global_date_range: Optional tuple of (start_date, end_date) to apply to all sources
    """
    turn_off()

    engine = get_database_engine()
    db_manager = DatabaseManager(engine)

    # Define data sources with their configurations
    data_sources = [
        DataSource(
            name="Oura Sleep",
            update_func=update_oura_sleep_data,
            model_class=SleepData,
            date_column='date',
            # custom_dates=(date(2024, 1, 1), date(2024, 12, 31))  # Uncomment to set custom dates for just Oura
        ),
        DataSource(
            name="Rize",
            update_func=update_rize_data,
            model_class=RizeSummary,  # Using RizeSummary as the primary model for date tracking
            date_column='date',
            # custom_dates=(date(2024, 1, 1), date(2024, 12, 31))  # Uncomment to set custom dates for just Rize
        )
    ]

    for source in data_sources:
        try:
            indicate_status("processing")
            
            # Determine which dates to use (priority: source custom dates > global dates > None)
            dates_to_use = source.custom_dates or global_date_range or (None, None)
            start_date, end_date = dates_to_use
            
            if start_date and end_date:
                logger.debug(f"Processing {source.name} with custom date range: {start_date} to {end_date}")
            else:
                logger.debug(f"Processing {source.name} using most recent data")
            
            source.update_func(db_manager, start_date, end_date)
            indicate_status("success", persist=True)
            
        except Exception as e:
            print(f"Error occurred in {source.name} update: {str(e)}")
            indicate_status("error", persist=True)
            set_color("green", brightness=20)

if __name__ == "__main__":
    # Option 1: Use most recent data for all sources (default)
    main()

    # Option 2: Set global date range for all sources
    # main((date(2024, 1, 1), date(2024, 12, 31)))