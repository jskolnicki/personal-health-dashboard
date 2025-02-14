# Personal Health Dashboard

A Flask-based personal dashboard that integrates multiple data sources into a centralized database with web-based visualization. Built with Flask-SQLAlchemy for database operations and provides automated data collection through various APIs.

## Project Overview

This project automates the collection, storage, and visualization of personal health and productivity data from various sources:

- **Oura Ring:** Sleep patterns, readiness, and activity data
- **Rize:** Productivity tracking and focus sessions
- **Google Sheets:** Custom data tracking (finances, vitals, etc.)

Key Features:
- Multi-user authentication system
- Secure integration credential storage
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
│   │   │   ├── templates/
│   │   │   └── routes.py
│   │   ├── home/               
│   │   │   ├── templates/
│   │   │   └── routes.py
│   │   └── rize/                # Feature-specific
│   │       ├── templates/
│   │       └── routes.py
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
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize database:
```bash
python database/create_db.py
```

## Blueprint Structure

Each feature is organized as a blueprint with:
- Routes and views (`routes.py`)
- Blueprint-specific templates
- Independent data models
- Feature-specific utilities

Example blueprint:
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

## Adding New Features

1. Create new blueprint directory
2. Define routes and templates
3. Add models to database/models.py
4. Register blueprint in app/__init__.py
5. Add any required API integrations