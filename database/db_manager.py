import os
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from database.models import SleepData, NapData

class DatabaseManager:
    def __init__(self, engine):
        self.Session = sessionmaker(bind=engine)

    def upsert_sleep_data(self, sleep_data):
        session = self.Session()
        try:
            for sleep in sleep_data:
                existing = session.query(SleepData).filter_by(
                    user_id=sleep['user_id'],
                    date=sleep['date']
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
                existing = session.query(NapData).filter_by(
                    user_id=nap['user_id'],
                    date=nap['date'],
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