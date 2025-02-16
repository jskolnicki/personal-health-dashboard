from datetime import datetime
from app.extensions import db
from utils.encryption import EncryptionManager
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy import Index

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sleep_data = db.relationship("SleepData", back_populates="user", lazy='dynamic')
    nap_data = db.relationship("NapData", back_populates="user", lazy='dynamic')
    integrations = db.relationship('UserIntegrations', back_populates='user')

    def __init__(self, username, email, password=None, **kwargs):
        super(Users, self).__init__(**kwargs)
        self.username = username
        self.email = email
        if password:
            self.set_password(password)

    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def get_id(self):
        """Required for Flask-Login."""
        return str(self.user_id)

    def __repr__(self):
        return f'<User {self.username}>'
    
class UserIntegrations(db.Model):
    __tablename__ = 'user_integrations'
    
    integration_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    integration_type = db.Column(db.String(50), nullable=False)
    encrypted_credentials = db.Column(db.LargeBinary)
    status = db.Column(db.String(20), default='active')
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to User
    user = db.relationship('Users', back_populates='integrations')

    def __init__(self, user_id, integration_type, credentials=None, status='active'):
        self.user_id = user_id
        self.integration_type = integration_type
        self.status = status
        if credentials:
            self.set_credentials(credentials)

    def set_credentials(self, credentials_dict):
        """
        Encrypt and store credentials.
        
        Args:
            credentials_dict (dict): Dictionary of credentials to encrypt
        """
        encryption_manager = EncryptionManager()
        self.encrypted_credentials = encryption_manager.encrypt_credentials(credentials_dict)

    def get_credentials(self):
        """
        Decrypt and return stored credentials.
        
        Returns:
            dict: Decrypted credentials dictionary
        """
        if not self.encrypted_credentials:
            return {}
            
        encryption_manager = EncryptionManager()
        return encryption_manager.decrypt_credentials(self.encrypted_credentials)

    def update_sync_status(self, success=True):
        """
        Update the last sync time and status.
        
        Args:
            success (bool): Whether the sync was successful
        """
        self.last_sync = datetime.utcnow()
        self.status = 'active' if success else 'error'
        db.session.commit()

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
    user = db.relationship("Users", back_populates="sleep_data")
    
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
    user = db.relationship("Users", back_populates="nap_data")
    
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

class DailyLogs(db.Model):
    __tablename__ = 'daily_logs'
    
    date = db.Column(db.Date, primary_key=True)
    content = db.Column(db.String(10000), nullable=False)
    summary = db.Column(db.String(1000), nullable=True)

    #Ratings
    day_score = db.Column(db.SmallInteger, nullable=True)
    productivity_score = db.Column(db.SmallInteger, nullable=True)
    
    # Tags
    activities = db.Column(db.String(500), nullable=True)
    social = db.Column(db.String(500), nullable=True)
    education = db.Column(db.String(500), nullable=True)
    mood = db.Column(db.String(500), nullable=True)
    custom_tags = db.Column(db.String(500), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_daily_logs_date', 'date'),
    )

class Reflections(db.Model):
    __tablename__ = 'reflections'
    
    reflection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    content = db.Column(db.String(10000), nullable=False)
    themes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_reflections_date', 'date'),
    )