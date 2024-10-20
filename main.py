import sys
import os
import logging
from datetime import date, timedelta

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

from data_sources.oura.processing import update_oura_sleep_data
from database.db_manager import DatabaseManager
from database.models import get_database_engine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the date range for processing data
end_date = date.today() + timedelta(days=1)  # date(2024, 1, 1)
start_date = end_date - timedelta(days=7)    # date(2025, 1, 1)

try:
    # Initialize database connection
    engine = get_database_engine()
    db_manager = DatabaseManager(engine)

    logging.info(f"Starting Oura sleep data update for date range: {start_date} to {end_date}")

    # Call the update_oura_sleep_data function
    update_oura_sleep_data(db_manager, start_date, end_date)

    logging.info("Oura sleep data update completed successfully")

except Exception as e:
    logging.error(f"An error occurred during Oura sleep data update: {str(e)}")
    sys.exit(1)