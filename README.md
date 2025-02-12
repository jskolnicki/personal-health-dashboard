# Personal Health Dashboard

This project is a Flask-based personal dashboard that integrates multiple data sources—such as Oura Ring, Rize, and Google Sheets—into a centralized database with web-based visualization. It uses Flask-SQLAlchemy for database operations and provides automated data collection through various APIs.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Data Sources](#data-sources)
4. [Database Integration](#database-integration)
5. [Dependencies & Setup](#dependencies--setup)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [Adding New Data Sources](#adding-new-data-sources)
9. [Troubleshooting](#troubleshooting)

## Project Overview

This project automates the collection, storage, and visualization of personal health and productivity data from various sources:

- **Oura Ring:** Sleep patterns, readiness, and activity data
- **Rize:** Productivity tracking and focus sessions
- **Google Sheets:** Custom data tracking (finances, vitals, etc.)

Key Features:
- Automated daily data collection
- Centralized MySQL database storage
- Web-based dashboards for visualization
- Modular design for easy extension

## Directory Structure

```
personal-health-dashboard/
├── app/                           # Flask web application
│   ├── __init__.py               # App initialization
│   ├── extensions.py             # Flask extensions (SQLAlchemy)
│   ├── blueprints/               # Flask blueprints
│   │   ├── dashboard/
│   │   ├── journal/
│   │   └── rize/
│   ├── static/
│   └── templates/
│
├── etl/                          # Data pipeline components
│   ├── __init__.py
│   ├── batch_job.py             # Daily data update script
│   └── data_sources/            # External data integrations
│       ├── oura/
│       │   ├── api.py           # Oura API client
│       │   └── sleep_data.py    # Sleep data processing
│       ├── rize/
│       │   ├── api.py           # Rize API client
│       │   └── rize.py          # Rize data processing
│       └── google_sheets/
│           ├── api.py           # Sheets API client
│           ├── finances.py      # Finance data processing
│           └── vitals.py        # Vitals data processing
│
├── database/                     # Database components
│   ├── models.py                # SQLAlchemy models
│   └── create_db.py             # Database initialization
│
├── utils/                        # Shared utilities
│   ├── logging_config.py        # Logging configuration
│   ├── date_utils.py            # Date handling utilities
│   └── status_manager.py        # Process status management
│
├── .env                         # Environment configuration
├── config.py                    # Application configuration
└── run.py                       # Flask application entry point
```

## Data Sources

### Oura Ring
- Sleep tracking (main sleep and naps)
- Data automatically categorized and processed
- Daily collection via Oura API

### Rize
- Productivity session tracking
- Daily summaries and focus metrics
- Real-time session data collection

### Google Sheets
- Custom data tracking (finances, vitals)
- Flexible spreadsheet integration
- Automated data import

## Database Integration

The project uses Flask-SQLAlchemy with these main models:

- `User`: Basic user information
- `SleepData` / `NapData`: Sleep tracking
- `RizeSession` / `RizeSummary`: Productivity data
- `FinanceData`: Financial transactions
- `Vitals`: Health metrics

## Dependencies & Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/personal-health-dashboard.git
cd personal-health-dashboard
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python database/create_db.py
```

## Configuration

Create a `.env` file in the project root:

```env
# Database
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_db_name

# API Keys
OURA_CLIENT_ID=your_oura_client_id
OURA_CLIENT_SECRET=your_oura_client_secret
OURA_ACCESS_TOKEN=your_oura_token
RIZE_API_KEY=your_rize_key

# Google Sheets
FINANCES_SHEET_ID=your_finances_sheet_id
VITALS_SHEET_ID=your_vitals_sheet_id

RIZE_API_KEY=your_rize_api_key
```

## Running the Application

1. Run the data collection job:
```bash
python -m etl.batch_job
```

2. Start the Flask application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Adding New Data Sources

1. Create a new directory in `data_sources/`
2. Add API client and data processing modules
3. Define database models in `database/models.py`
4. Add the source to `main.py`

Example structure for a new data source:
```
data_sources/new_source/
├── __init__.py
├── api.py          # API client
└── processing.py   # Data processing
```

## Troubleshooting

Common issues and solutions:

1. Database Connection:
   - Verify credentials in `.env`
   - Check if MySQL server is running
   - Ensure database exists

2. API Issues:
   - Validate API keys in `.env`
   - Check API rate limits
   - Verify network connectivity

3. Data Processing:
   - Check logs in `logs/personal_health.log`
   - Verify data source format hasn't changed
   - Ensure all required fields are present

Logs are stored in `logs/personal_health.log`. Enable DEBUG level logging in `utils/logging_config.py` for more detailed output.