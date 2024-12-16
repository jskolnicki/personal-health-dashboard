import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, Column, Integer, SmallInteger, String, DateTime, Date, ForeignKey, UniqueConstraint, Float, Index, Numeric, Boolean
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    sleep_data = relationship("SleepData", back_populates="user")
    nap_data = relationship("NapData", back_populates="user")

class SleepData(Base):
    __tablename__ = 'sleep_data'
    
    sleep_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    bedtime_start = Column(DateTime, nullable=False)
    bedtime_end = Column(DateTime, nullable=False)
    sleep_start = Column(DateTime, nullable=False)
    sleep_end = Column(DateTime, nullable=False)
    timezone_offset = Column(SmallInteger, nullable=False)
    total_sleep_duration = Column(Integer, nullable=False)
    latency = Column(Integer, nullable=True)
    time_in_bed = Column(Integer, nullable=False)
    sleep_awake_time = Column(Integer, nullable=False)
    midsleep_awake_time = Column(Integer, nullable=False)
    deep_sleep_duration = Column(Integer, nullable=False)
    light_sleep_duration = Column(Integer, nullable=False)
    rem_sleep_duration = Column(Integer, nullable=False)
    restless_periods = Column(Integer, nullable=False)
    average_heart_rate = Column(Float, nullable=True)
    average_hrv = Column(Float, nullable=True)
    
    user = relationship("User", back_populates="sleep_data")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uix_user_date'),
    )

class NapData(Base):
    __tablename__ = 'nap_data'
    
    nap_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    bedtime_start = Column(DateTime, nullable=False)
    bedtime_end = Column(DateTime, nullable=False)
    sleep_start = Column(DateTime, nullable=False)
    sleep_end = Column(DateTime, nullable=False)
    timezone_offset = Column(SmallInteger, nullable=False)
    total_sleep_duration = Column(Integer, nullable=False)
    latency = Column(Integer, nullable=True)
    time_in_bed = Column(Integer, nullable=False)
    sleep_awake_time = Column(Integer, nullable=False)
    midsleep_awake_time = Column(Integer, nullable=False)
    deep_sleep_duration = Column(Integer, nullable=False)
    light_sleep_duration = Column(Integer, nullable=False)
    rem_sleep_duration = Column(Integer, nullable=False)
    restless_periods = Column(Integer, nullable=False)
    average_heart_rate = Column(Float, nullable=True)
    average_hrv = Column(Float, nullable=True)
    
    user = relationship("User", back_populates="nap_data")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', 'bedtime_start', name='uix_user_date_bedtime'),
    )

class RizeSession(Base):
    __tablename__ = 'rize_sessions'
    
    session_id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    type = Column(String(50), nullable=True)
    source = Column(String(50), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_rize_sessions_date', 'date'),  # For date range queries
        Index('idx_rize_sessions_type', 'type'),  # For filtering by session type
        Index('idx_rize_sessions_source', 'source'),  # For filtering by application
        Index('idx_rize_sessions_date_type', 'date', 'type'),  # For combined date+type queries
        Index('idx_rize_sessions_start_time', 'start_time'),  # For filtering sessions after X time
        Index('idx_rize_sessions_end_time', 'end_time'),  # For filtering sessions before Y time
        Index('idx_rize_sessions_timespan', 'start_time', 'end_time')  # For time range overlaps
    )

class RizeSummary(Base):
    __tablename__ = 'rize_summaries'
    
    date = Column(Date, primary_key=True)
    wday = Column(String(10), nullable=False)
    focus_time = Column(Integer, nullable=False)
    break_time = Column(Integer, nullable=False)
    meeting_time = Column(Integer, nullable=False)
    tracked_time = Column(Integer, nullable=False)
    work_hours = Column(Integer, nullable=False)
    daily_meeting_time_average = Column(Integer, nullable=False)
    daily_tracked_time_average = Column(Integer, nullable=False)
    daily_focus_time_average = Column(Integer, nullable=False)
    daily_work_hours_average = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_rize_summaries_date', 'date'),  # Already have this one
        Index('idx_rize_summaries_wday', 'wday'),  # For day-of-week analysis
        Index('idx_rize_summaries_date_wday', 'date', 'wday'),  # For combined queries
    )

class FinanceData(Base):
    __tablename__ = 'finances'
    
    transaction_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(String(100), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    gift_type = Column(String(10), nullable=True)
    person = Column(String(100), nullable=True)
    notes = Column(String(1000), nullable=True)
    account_name = Column(String(100), nullable=True)
    is_date = Column(Boolean, default=False, nullable=False)
    is_vacation = Column(Boolean, default=False, nullable=False)
    is_birthday = Column(Boolean, default=False, nullable=False)
    is_christmas = Column(Boolean, default=False, nullable=False)
    transaction_hash = Column(String(32), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_finances_date', 'transaction_date'),
        Index('idx_finances_category', 'category'),
    )

class Vitals(Base):
    __tablename__ = 'vitals'
    
    date = Column(Date, primary_key=True)
    wake_up_time = Column(DateTime, nullable=True)
    sleep_minutes = Column(Integer, nullable=True)
    weight = Column(Float, nullable=True)
    nap_minutes = Column(Integer, nullable=True)
    drinks = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

def get_database_engine():
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    port = os.getenv('DB_PORT', '3306')  # Default to 3306 if not specified
    
    if not all([username, password, host, db_name]):
        raise ValueError("Missing database configuration. Please check your .env file.")
    
    connection_string = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{db_name}"
    
    try:
        engine = create_engine(connection_string)
        # Test the connection
        with engine.connect() as connection:
            print(f"Successfully connected to database: {db_name}")
        return engine
    except SQLAlchemyError as e:
        print(f"Error connecting to the database. Details: {str(e)}")
        raise

def create_tables(engine):
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    tables_to_create = [table for name, table in Base.metadata.tables.items() if name not in existing_tables]
    
    if tables_to_create:
        Base.metadata.create_all(engine, tables=tables_to_create)
        print(f"Created tables: {', '.join(table.name for table in tables_to_create)}")
    else:
        print("All tables already exist.")