# Personal Health Analytics

This project aggregates and analyzes personal health data, primarily from the Oura Ring API and Google Sheets, with plans to incorporate additional data sources in the future.

## Features

- Daily automated data retrieval from Oura Ring API
- Integration with Google Sheets for additional data sources (finances, weight tracking, etc.)
- Processing and storage of sleep and nap data in a local MySQL database
- Modular design for easy integration of future data sources
- Automated logging system for tracking data processing and potential issues

## Project Structure

```
project_root/
├── data_sources/
│   ├── oura/
│   │   ├── api.py
│   │   └── processing.py
│   └── google_sheets/
│       ├── api.py
│       └── finances.py
├── database/
│   ├── create_db.py
│   ├── db_manager.py
│   └── models.py
├── utils/
│   ├── blinkstick.py
│   └── logging_config.py
├── .env
├── .gitignore
├── main.py
└── requirements.txt
```

- `data_sources/`: API integrations and processing scripts
  - `oura/`: Oura Ring API integration
  - `google_sheets/`: Google Sheets API integration for additional data sources
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
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

6. Set up Google Sheets API access:
   - Go to the [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Google Sheets API
   - Create OAuth 2.0 credentials (Desktop application)
   - Add yourself as a test user in the OAuth consent screen
   - Copy your Client ID and Client Secret to the `.env` file

7. Run the database setup script:
   ```
   python database/create_db.py
   ```
8. Run the main script to process data:
   ```
   python main.py
   ```

Note: The first time you run the application with Google Sheets integration, it will prompt you to authenticate through your browser. This will create a `token.json` file in the `data_sources/google_sheets` directory for future authentication.

## Google Sheets Integration

This project supports pulling data from Google Sheets, allowing you to integrate any personal data you track in spreadsheets. Common use cases might include weight tracking, workout logs, financial data, or any other metrics you track.

### Setting up Google Sheets API

1. Create and configure your Google Cloud Project:
   - Go to the [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Google Sheets API for your project

2. Create a Service Account:
   - In Google Cloud Console, go to "APIs & Services" > "Credentials"
   - Click "+ CREATE CREDENTIALS" and select "Service Account"
   - Fill in a name for your service account (e.g., "health-dashboard-bot")
   - Click "CREATE"
   - Skip the optional steps about roles/access
   - Click "DONE"

3. Generate Service Account Key:
   - Click on the service account name in the credentials list
   - Go to the "KEYS" tab
   - Click "ADD KEY" > "Create new key"
   - Choose "JSON" format
   - Click "CREATE" to download the key file

4. Set up the credentials:
   - Rename the downloaded JSON file to `sheets-credentials.json`
   - Place it in the `data_sources/google_sheets` directory
   - Add `sheets-credentials.json` to your `.gitignore` file

5. Share your Google Sheets:
   - Find the service account email in the JSON file (ends with `.iam.gserviceaccount.com`)
   - Open each Google Sheet you want to access
   - Click the "Share" button
   - Add the service account email and give it "Viewer" access
   - Click "Share"

### Integrating Your Data

To integrate your own Google Sheets:

1. Get your Sheet ID:
   - Open your Google Sheet
   - Copy the ID from the URL: `https://docs.google.com/spreadsheets/d/[YOUR-SHEET-ID]/edit`
   - Add the ID to your `.env` file:
     ```
     YOUR_DATA_SHEET_ID=your_sheet_id_here
     ```

2. Create a new processing file:
   - Create a new Python file in `data_sources/google_sheets/` for your data source
   - Use the `GoogleSheetsAPI` class to fetch your data
   - Configure the sheet name and range according to your spreadsheet structure

Example processing file structure:
```python
def get_data():
    api = GoogleSheetsAPI()
    raw_data = api.get_sheet_data(
        spreadsheet_id=os.getenv('YOUR_DATA_SHEET_ID'),
        range_name='YourSheetName!A:E'  # Adjust range as needed
    )
    # Process your data here
    return processed_data
```

### Best Practices

1. Sheet Structure:
   - Use the first row for column headers
   - Keep data formats consistent within columns
   - Avoid merged cells and complex formatting

2. Data Processing:
   - Create separate processing files for different types of data
   - Include data validation and error handling
   - Document any specific data format requirements

3. Security:
   - Never commit credentials to version control
   - Use environment variables for sensitive information
   - Regularly review service account access

Remember to adjust the sheet names, ranges, and processing logic to match your specific data structure and requirements.

## Data Processing

The `main.py` script automates the following processes:
- Retrieves sleep data from the Oura API for the last 3 days by default
- Pulls data from configured Google Sheets
- Processes and categorizes the data
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