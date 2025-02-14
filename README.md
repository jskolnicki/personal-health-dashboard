# Personal Health Dashboard

A Flask-based personal dashboard that integrates multiple data sources into a centralized database with web-based visualization. Built with Flask-SQLAlchemy for database operations and provides automated data collection through various APIs.

## Project Overview

This project automates the collection, storage, and visualization of personal health, productivity, and lifestyle data from various sources:

- **Oura Ring:** Sleep patterns, readiness, and activity data
- **Rize:** Productivity tracking and focus sessions
- **Journal:** Daily logs and reflections with tagging system
- **Google Sheets:** Custom data tracking (finances, vitals, etc.)

Key Features:
- Multi-user authentication system
- OAuth-based service integrations
- Secure credential storage and encryption
- Automated daily data collection per user
- Centralized MySQL database storage
- Web-based dashboards for visualization
- Blueprint-based modular design

## Directory Structure

```
personal-health-dashboard/
├── app/
│   ├── __init__.py               # App initialization
│   ├── extensions.py             # Flask extensions
│   ├── templates/
│   │   └── base.html            # Base template
│   ├── blueprints/              # Feature modules
│   │   ├── auth/                # Authentication
│   │   ├── home/                # Dashboard home
│   │   ├── integrations/        # Service connections
│   │   ├── journal/             # Daily logging
│   │   └── rize/                # Productivity tracking
│   └── static/                  # Static assets
│
├── database/
│   ├── models.py                # SQLAlchemy models
│   └── create_db.py             # DB initialization
│
├── etl/                         # Data collection
│   ├── batch_job.py             # Main ETL runner
│   └── data_sources/           
│       ├── oura/
│       ├── rize/
│       └── google_sheets/
│
├── utils/                       # Shared utilities
│   ├── encryption.py            # Security helpers
│   ├── logging_config.py
│   └── date_utils.py
│
├── .env                         # Configuration
└── config.py                    # App settings
```

## Core Components

### Authentication
- Blueprint-based auth system with registration/login
- Secure password hashing using Werkzeug
- Flask-Login for session management
- Protected routes for personal data

### Integration Management
- OAuth 2.0 flow for service connections
- Secure storage of API credentials using encryption
- Per-user integration configuration
- Integration status tracking
- Automated sync status updates

### Data Collection
- Automated batch processing for all users
- User-specific date range tracking
- Independent processing queues
- Error handling and logging

### Database Models
- `Users`: Authentication and user management
- `UserIntegrations`: API credentials and sync status
- `SleepData/NapData`: Sleep tracking
- `RizeSessions/RizeSummaries`: Productivity
- `DailyLogs/Reflections`: Journal entries
- `Finances/Vitals`: Custom tracking

## Setup and Configuration

1. Environment setup:
```env
# Security
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key

# Database
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_db_name

# Oura
OURA_CLIENT_ID=your_oura_client_id
OURA_CLIENT_SECRET=your_oura_client_secret
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize database:
```bash
python database/create_db.py
```

## Blueprint Architecture

Each feature is organized as a blueprint containing:
- Routes and views (`routes.py`)
- Feature-specific templates
- Independent data models
- Utility functions

This modular structure allows for:
- Independent feature development
- Clear separation of concerns
- Easy addition of new features
- Maintainable codebase

Example blueprint structure:
```
blueprints/feature_name/
├── templates/           # Feature templates
├── routes.py           # URL routes
└── __init__.py         # Blueprint setup
```

## Running the Application

1. Run data collection:
```bash
python -m etl.batch_job
```

2. Start Flask app:
```bash
python run.py
```

## Development Guide

### Adding New Features

1. Create new blueprint directory
2. Define routes and templates
3. Add models to database/models.py
4. Register blueprint in app/__init__.py
5. Add any required API integrations

### Best Practices

- Follow blueprint pattern for new features
- Maintain consistent model relationships
- Use appropriate data types and indexing
- Keep API integrations modular
- Implement proper error handling
- Follow established UI patterns

## Security Considerations

- All user credentials are encrypted
- API tokens stored securely
- Password hashing for user accounts
- Protected routes require authentication
- CSRF protection enabled
- Secure session management