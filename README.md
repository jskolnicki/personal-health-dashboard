# Personal Health Analytics

This project aggregates and analyzes personal health data, primarily from the Oura Ring API, with plans to incorporate additional data sources in the future.

## Features

- Daily automated data retrieval from Oura Ring API
- Processing and storage of sleep and nap data in a local MySQL database
- Modular design for easy integration of future data sources
- Automated logging system for tracking data processing and potential issues

## Project Structure

```
project_root/
├── data_sources/
│   └── oura/
│       ├── api.py
│       └── processing.py
├── database/
│   ├── create_db.py
│   ├── db_manager.py
│   └── models.py
├── utils/
│   └── logging_config.py
├── .env
├── .gitignore
├── main.py
└── requirements.txt
```

- `data_sources/`: API integrations and processing scripts
- `database/`: Database models, management, and creation scripts
- `utils/`: Utility functions, including logging configuration
- `main.py`: Main execution script for data processing
- `.env`: Environment variables (not in version control)
- `requirements.txt`: Project dependencies

## Setup

This project was developed and tested with Python 3.10. Ensure you have Python 3.8 or higher installed before proceeding.

1. Clone the repository
2. Set up a virtual environment:
   ```
   python -m venv vitals
   source vitals/bin/activate  # Linux/Mac
   vitals\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up your MySQL database
5. Create a `.env` file in the root directory with the following content:
   ```
   DB_USERNAME=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_HOST=localhost
   DB_NAME=your_database_name
   DB_PORT=your_port_number
   OURA_ACCESS_TOKEN=your_oura_access_token
   ```
   Replace the values with your actual database credentials and Oura API token.
6. Run the database setup script:
   ```
   python database/create_db.py
   ```
7. Run the main script to process data:
   ```
   python main.py
   ```

## Database Schema

The project uses two main tables:

1. `sleep_data`: Stores nightly sleep information
2. `nap_data`: Stores daytime nap information

Both tables include detailed sleep metrics such as sleep duration, sleep stages, heart rate, and HRV.

## Data Processing

The `main.py` script automates the following process:
- Retrieves sleep data from the Oura API for the last 3 days by default
- Processes and categorizes the data into sleep and nap records
- Upserts the processed data into the database

To modify the date range for data retrieval, adjust the `start_date` and `end_date` variables in `main.py`.

## Logging

This application uses a centralized logging system. Logs are written to 'personal_health_analytics.log' in the 'logs' directory, which is created automatically if it doesn't exist. 

Log messages include timestamps, log levels, and contextual information about the operation being performed. Both file and console logging are enabled by default.

Note: Log files are not tracked by git.

## Running the Application

For daily data processing, run:

```
python main.py
```

This will process data for the last 3 days by default. To process data for a specific date range, modify the `start_date` and `end_date` variables in `main.py`.

## Future Plans

- Add data visualization capabilities
- Implement trend analysis and insights generation
- Integration with additional data sources

## Troubleshooting

If you encounter any issues:
1. Check the log files in the `logs` directory for error messages.
2. Ensure your `.env` file contains the correct database credentials and API tokens.
3. Verify that your database is running and accessible.

For any persistent problems, please open an issue in the project repository.