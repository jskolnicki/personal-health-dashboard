# Personal Data Dashboard

This repository is a template and example for building a personal dashboard that integrates multiple data sources—such as Oura, Rize, and Google Sheets—into a single, centralized view. It uses Python, SQLAlchemy, and Flask to automate daily data collection and present visual summaries via web-based dashboards.

**Note:** This is not a production-ready solution. It’s a starting point, offering patterns and examples that you can extend or modify to meet your own data needs. You can pick and choose the components you find valuable—some users might only want to use the Oura integration, others might focus on Rize sessions, and others on Google Sheets data, etc.

## Table of Contents

1. [Project Overview](#project-overview)  
2. [File & Directory Structure](#file--directory-structure)  
3. [Data Sources](#data-sources)  
   - [Oura](#oura)  
   - [Rize](#rize)  
   - [Google Sheets](#google-sheets)  
   *(Add more sources here as your project scales)*
4. [Database Integration](#database-integration)  
5. [Daily Batch Job (main.py)](#daily-batch-job-mainpy)  
6. [Web Server & Dashboards](#web-server--dashboards)  
7. [Dependencies & Setup](#dependencies--setup)  
8. [Configuration & Environment Variables](#configuration--environment-variables)  
9. [Extending & Adding New Data Sources](#extending--adding-new-data-sources)  
10. [Troubleshooting & Logging](#troubleshooting--logging)  
11. [Future Plans & Scalability](#future-plans--scalability)

---

## Project Overview

This project automates the retrieval, storage, and visualization of personal health and productivity data from various sources. After data is pulled daily (or on a schedule you define), it is processed and stored in a database. A Flask-based web server then provides dashboards to view trends, summaries, and insights.

**Key concepts:**

- **Automated Data Pulling:** The `main.py` script acts as a batch job to update data from all configured data sources.
- **Modular Data Sources:** Each data source (Oura, Rize, Google Sheets, etc.) resides in its own directory with dedicated API clients and processing scripts.
- **Database Persistence:** Data is normalized and stored in a MySQL (or other SQL-compatible) database using SQLAlchemy models.
- **Dashboarding & Visualization:** A Flask application hosts templates and routes to visualize the ingested data.

---

## File & Directory Structure

The repository is organized to separate logic by function and data source. Below is a simplified overview:

```
app
├── routes
│   ├── __init__.py
│   └── dashboard.py
├── static
└── templates
    ├── rize_dashboard.html
    ├── __init__.py
    └── config.py

data_sources
├── google_sheets
│   ├── __init__.py
│   ├── api.py
│   ├── processing.py
│   └── sheets-credentials.json
├── oura
│   ├── __init__.py
│   ├── api.py
│   └── sleep_data.py
└── rize
    ├── __init__.py
    ├── api.py
    ├── rize.py
    └── init_.py
database
├── __pycache__
├── __init__.py
├── create_db.py
├── db_manager.py
└── models.py

logs
└── personal_health.log

utils
├── __pycache__
├── blinkstick.py
└── logging_config.py

.gitignore
CODEOWNERS
main.py
README.md
requirements.txt
run.py
```

This structure makes it easier to maintain and scale the codebase. Each data source is self-contained, while `main.py` orchestrates updates.

---

## Data Sources

### Oura

- **Location:** `data_sources/oura`
- **Files:** 
  - `api.py` handles authentication and data retrieval from the Oura API.
  - `sleep_data.py` processes raw Oura sleep sessions into a standardized format before storing them.
  
**Data Flow:**  
`main.py` → calls `update_oura_sleep_data` → `oura/api.py` retrieves raw JSON → `oura/sleep_data.py` processes and categorizes sleep and nap sessions → `db_manager.upsert_sleep_data()` stores results.

If you only want Oura data, focus on:
- Setting up Oura API credentials in `.env`.
- Running `main.py` to pull and store sleep data.
- Accessing the Flask dashboard routes to visualize.

### Rize

- **Location:** `data_sources/rize`
- **Files:** 
  - `api.py` manages Rize API calls.
  - `rize.py` processes session-level and daily summary data.
  
**Data Flow:**  
`main.py` → `update_rize_data` → `rize/api.py` → `rize/rize.py` → store in `rize_sessions` and `rize_summaries` tables.

If you only want Rize data, configure the Rize API key and run the main job. The `rize_dashboard.html` template provides a starting point for visualization.

### Google Sheets

- **Location:** `data_sources/google_sheets`
- **Files:**
  - `api.py` uses Google service account credentials to read from Sheets.
  - `processing.py` (if implemented) transforms the raw sheet data into records suitable for the database.
  
**Data Flow:**  
`main.py` → `update_vitals_data` (example) → `google_sheets/api.py` fetches data → `processing.py` cleans and prepares data → `db_manager` inserts it.

If your data is in a spreadsheet, you can easily adapt these patterns to ingest any tabular data source.

*(Add more data sources here as they are introduced.)*

---

## Database Integration

The project uses SQLAlchemy for ORM-based database interactions. The schema is defined in `database/models.py`. For example:

- **Users:** Basic user info and references to their sleep/nap data.
- **SleepData / NapData:** Detailed sleep sessions, durations, phases, etc.
- **RizeSession / RizeSummary:** Productivity session data and daily summaries from Rize.

To set up:
1. Configure database credentials in `.env` (see [Configuration & Environment Variables](#configuration--environment-variables)).
2. Run `python database/create_db.py` to create tables (if they do not already exist).
   
The `db_manager.py` provides convenience methods for inserting/updating (“upserting”) data.

---

## Daily Batch Job (main.py)

`main.py` is the main entry point for updating data. It:

- Connects to the database.
- Iterates through each data source you’ve configured.
- Pulls new data since the last recorded date.
- Processes and upserts that data into the database.
- Logs results and errors.

**How to run:**  
```bash
python main.py
```

Set this up as a daily cron job or scheduled task to keep your dashboard data fresh.

## Web Server & Dashboards

A simple Flask application (run via `run.py`) hosts web pages to visualize your data:

* **Templates:** Located in `app/templates/`.
* **Routes:** Defined in `app/routes/dashboard.py` and others.

This is intentionally minimal—customize templates, add routes, or integrate with a dashboarding tool as needed. The idea is to provide a starting point to serve data insights via a local or remote web server.

**How to run the web server:**

```bash
python run.py
```

Then open `http://localhost:5000` in your browser.

## Dependencies & Setup

**Installation Steps:**

1. Clone the repository.
2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file (see next section).
5. Initialize the database:

```bash
python database/create_db.py
```

6. Run the daily update:

```bash
python main.py
```

7. Run the Flask server:

```bash
python run.py
```

## Configuration & Environment Variables

All sensitive information (API keys, database credentials) and other configurations are stored in a `.env` file at the project root. For example:

```makefile
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_db_name
OURA_ACCESS_TOKEN=your_oura_access_token
RIZE_API_KEY=your_rize_api_key
VITALS_SHEET_ID=your_google_sheet_id
```

Update these values as needed. Never commit the `.env` file to public repositories.

## Extending & Adding New Data Sources

The repository is designed to be modular. To add a new data source:

1. Create a new directory under `data_sources/` (e.g. `data_sources/fitbit`).
2. Add an `api.py` file to handle API retrieval.
3. Add a processing script to convert raw data into a standardized format.
4. Extend `database/models.py` to include new tables if needed.
5. Update `main.py` to include a new `DataSource` object with your update function.

By following these patterns, you keep your code organized and make it easier to scale as you incorporate more data streams.

## Troubleshooting & Logging

* Logs are stored in `logs/personal_health.log`.
* Check logs for any data retrieval or database insertion errors.
* For API-related issues, ensure credentials are correct in `.env`.
* If the database fails to connect, verify network settings and credentials in the `.env` file.
* Missing data is often due to API rate limits or insufficient permissions—double-check the source's developer docs.

## Future Plans & Scalability

This README and repository structure anticipates growth:

* **More Data Sources:** As you add more APIs, keep them isolated in their own directories, following the existing pattern.
* **More Dashboards:** Add templates and routes under `app/` to visualize each data set differently.
* **Refined Models:** Over time, refine your SQLAlchemy models and add indexes or constraints as needed.
* **Scheduled Automation:** Integrate with a scheduler (cron, Airflow, etc.) to run `main.py` at regular intervals.
* **CI/CD Integration:** Set up GitHub Actions or other CI tools to test code changes, lint code, and ensure database migrations run smoothly.

The current implementation is a starting point. With careful planning and incremental improvements, you can evolve this codebase into a robust personal analytics dashboard.

**Start small**—pull one data source, visualize it, and iterate from there. Good luck, and have fun exploring your personal data!