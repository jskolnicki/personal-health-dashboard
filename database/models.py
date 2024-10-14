import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint, Float
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
    total_sleep_duration = Column(Integer, nullable=False)  # in seconds
    time_in_bed = Column(Integer, nullable=False)  # in seconds
    sleep_awake_time = Column(Integer, nullable=False)  # in seconds
    deep_sleep_duration = Column(Integer, nullable=False)  # in seconds
    light_sleep_duration = Column(Integer, nullable=False)  # in seconds
    rem_sleep_duration = Column(Integer, nullable=False)  # in seconds
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
    total_sleep_duration = Column(Integer, nullable=False)  # in seconds
    time_in_bed = Column(Integer, nullable=False)  # in seconds
    sleep_awake_time = Column(Integer, nullable=False)  # in seconds
    deep_sleep_duration = Column(Integer, nullable=False)  # in seconds
    light_sleep_duration = Column(Integer, nullable=False)  # in seconds
    rem_sleep_duration = Column(Integer, nullable=False)  # in seconds
    restless_periods = Column(Integer, nullable=False)
    average_heart_rate = Column(Float, nullable=True)
    average_hrv = Column(Float, nullable=True)
    
    user = relationship("User", back_populates="nap_data")

    __table_args__ = (
        UniqueConstraint('user_id', 'date', 'bedtime_start', name='uix_user_date_bedtime'),
    )

def create_database():
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
        # Try to connect to the database
        with engine.connect() as connection:
            print(f"Successfully connected to database: {db_name}")
        
        # If connection successful, create tables
        Base.metadata.create_all(engine, checkfirst=True)
        print("Database tables created or updated successfully.")
        
        return engine
    except SQLAlchemyError as e:
        print(f"Error connecting to the database. Details: {str(e)}")
        print(f"Connection string used: {connection_string}")
        raise