import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

from datetime import date, timedelta
from typing import Dict, Type, Optional, Tuple
from sqlalchemy import func
from app.extensions import db

DEFAULT_START_DATES: Dict[str, date] = {
    'Vitals': date(2018, 12, 25),
    'Finances': date(2021, 1, 19),
    'RizeSummaries': date(2024, 2, 18),
    'RizeSessions': date(2024, 2, 18),
    'SleepData': date(2024, 6, 9)
}

def get_date_range(model_class: Type, date_column: str = 'date') -> Tuple[date, date]:
    """
    Get the date range from the most recent record to today.
    
    Args:
        model_class: SQLAlchemy model class
        date_column: Name of the date column to query
        
    Returns:
        Tuple[date, date]: (start_date, end_date)
    """
    last_record_date = db.session.query(
        func.max(getattr(model_class, date_column))
    ).scalar()
    
    end_date = date.today() + timedelta(days=1)  # Include today's data
    
    if last_record_date:
        # Handle potential pandas Timestamp
        if hasattr(last_record_date, 'date'):
            last_record_date = last_record_date.date()
        elif isinstance(last_record_date, str):
            last_record_date = date.fromisoformat(last_record_date)
            
        start_date = last_record_date + timedelta(days=1)
        if start_date > end_date:
            return end_date, end_date
    else:
        model_name = model_class.__name__
        start_date = DEFAULT_START_DATES.get(model_name, date(2018, 1, 1))
    
    return start_date, end_date