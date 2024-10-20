from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from data_sources.oura.processing import update_oura_sleep_data
from database.db_manager import DatabaseManager
from database.models import get_database_engine
from utils.logging_config import setup_logging
from utils.blinkstick import indicate_status, turn_off, set_color

# Set up logging
logger = setup_logging()

# Set the date range for processing data
end_date = date.today() + timedelta(days=1)
start_date = end_date - timedelta(days=3)

# Uncomment and modify these lines to set specific dates
# end_date = date(2024, 1, 1)
# start_date = date(2023, 1, 1)

def main():
    turn_off()  # Reset BlinkStick from previous run
    logger.debug(f"Processing data from {start_date} to {end_date}")

    engine = get_database_engine()
    db_manager = DatabaseManager(engine)

    data_sources = [
        ("Oura Sleep", update_oura_sleep_data),
        # Add other data sources here: ("Source Name", update_function)
    ]

    for source_name, update_function in data_sources:
        try:
            indicate_status("processing")
            update_function(db_manager, start_date, end_date)
            indicate_status("success", persist=True)
        except Exception as e:
            # Errors are logged inside the individual functions
            # Print here for immediate visibility when running the script
            print(f"Error occurred in {source_name} update: {str(e)}")
            indicate_status("error", persist=True)
            set_color("green", brightness=20)

if __name__ == "__main__":
    main()