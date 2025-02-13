from datetime import datetime
from app.extensions import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy import Index

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Relationships
    sleep_data = db.relationship("SleepData", back_populates="user", lazy='dynamic')
    nap_data = db.relationship("NapData", back_populates="user", lazy='dynamic')

class SleepData(db.Model):
    __tablename__ = 'sleep_data'
    
    sleep_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    bedtime_start = db.Column(db.DateTime, nullable=False)
    bedtime_end = db.Column(db.DateTime, nullable=False)
    sleep_start = db.Column(db.DateTime, nullable=False)
    sleep_end = db.Column(db.DateTime, nullable=False)
    timezone_offset = db.Column(db.SmallInteger, nullable=False)
    total_sleep_duration = db.Column(db.Integer, nullable=False)
    latency = db.Column(db.Integer, nullable=True)
    time_in_bed = db.Column(db.Integer, nullable=False)
    sleep_awake_time = db.Column(db.Integer, nullable=False)
    midsleep_awake_time = db.Column(db.Integer, nullable=False)
    deep_sleep_duration = db.Column(db.Integer, nullable=False)
    light_sleep_duration = db.Column(db.Integer, nullable=False)
    rem_sleep_duration = db.Column(db.Integer, nullable=False)
    restless_periods = db.Column(db.Integer, nullable=False)
    average_heart_rate = db.Column(db.Float, nullable=True)
    average_hrv = db.Column(db.Float, nullable=True)
    
    # Relationships
    user = db.relationship("User", back_populates="sleep_data")
    
    # Constraints and Indexes
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uix_user_date'),
    )

class NapData(db.Model):
    __tablename__ = 'nap_data'
    
    nap_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    bedtime_start = db.Column(db.DateTime, nullable=False)
    bedtime_end = db.Column(db.DateTime, nullable=False)
    sleep_start = db.Column(db.DateTime, nullable=False)
    sleep_end = db.Column(db.DateTime, nullable=False)
    timezone_offset = db.Column(db.SmallInteger, nullable=False)
    total_sleep_duration = db.Column(db.Integer, nullable=False)
    latency = db.Column(db.Integer, nullable=True)
    time_in_bed = db.Column(db.Integer, nullable=False)
    sleep_awake_time = db.Column(db.Integer, nullable=False)
    midsleep_awake_time = db.Column(db.Integer, nullable=False)
    deep_sleep_duration = db.Column(db.Integer, nullable=False)
    light_sleep_duration = db.Column(db.Integer, nullable=False)
    rem_sleep_duration = db.Column(db.Integer, nullable=False)
    restless_periods = db.Column(db.Integer, nullable=False)
    average_heart_rate = db.Column(db.Float, nullable=True)
    average_hrv = db.Column(db.Float, nullable=True)
    
    # Relationships
    user = db.relationship("User", back_populates="nap_data")
    
    # Constraints and Indexes
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', 'bedtime_start', name='uix_user_date_bedtime'),
    )

class RizeSessions(db.Model):
    __tablename__ = 'rize_sessions'
    
    session_id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(1000), nullable=True)
    type = db.Column(db.String(50), nullable=True)
    source = db.Column(db.String(50), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_rize_sessions_date', 'date'),
        Index('idx_rize_sessions_type', 'type'),
        Index('idx_rize_sessions_source', 'source'),
        Index('idx_rize_sessions_date_type', 'date', 'type'),
        Index('idx_rize_sessions_start_time', 'start_time'),
        Index('idx_rize_sessions_end_time', 'end_time'),
        Index('idx_rize_sessions_timespan', 'start_time', 'end_time')
    )

class RizeSummaries(db.Model):
    __tablename__ = 'rize_summaries'
    
    date = db.Column(db.Date, primary_key=True)
    wday = db.Column(db.String(10), nullable=False)
    focus_time = db.Column(db.Integer, nullable=False)
    break_time = db.Column(db.Integer, nullable=False)
    meeting_time = db.Column(db.Integer, nullable=False)
    tracked_time = db.Column(db.Integer, nullable=False)
    work_hours = db.Column(db.Integer, nullable=False)
    daily_meeting_time_average = db.Column(db.Integer, nullable=False)
    daily_tracked_time_average = db.Column(db.Integer, nullable=False)
    daily_focus_time_average = db.Column(db.Integer, nullable=False)
    daily_work_hours_average = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_rize_summaries_date', 'date'),
        Index('idx_rize_summaries_wday', 'wday'),
        Index('idx_rize_summaries_date_wday', 'date', 'wday'),
    )

class Finances(db.Model):
    __tablename__ = 'finances'
    
    transaction_hash = db.Column(db.String(32), primary_key=True)
    transaction_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    gift_type = db.Column(db.String(10), nullable=True)
    person = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.String(1000), nullable=True)
    account_name = db.Column(db.String(100), nullable=True)
    is_date = db.Column(db.Boolean, default=False, nullable=False)
    is_vacation = db.Column(db.Boolean, default=False, nullable=False)
    is_birthday = db.Column(db.Boolean, default=False, nullable=False)
    is_christmas = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(TIMESTAMP, server_default=func.now())
    updated_at = db.Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_finances_date', 'transaction_date'),
        Index('idx_finances_category', 'category'),
    )

class Vitals(db.Model):
    __tablename__ = 'vitals'
    
    date = db.Column(db.Date, primary_key=True)
    wake_up_time = db.Column(db.DateTime, nullable=True)
    sleep_minutes = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    nap_minutes = db.Column(db.Integer, nullable=True)
    drinks = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())