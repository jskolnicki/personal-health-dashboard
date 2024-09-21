# Personal Health Analytics

This project aggregates and analyzes personal health data, primarily from the Oura Ring API, with plans to incorporate additional data sources in the future.

## Features

- Daily data retrieval from Oura Ring API
- Storage of sleep, activity, and readiness data in a local database
- Modular design for easy integration of future data sources

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in a `.env` file:
   ```
   DATABASE_URL=your_database_url
   OURA_API_KEY=your_oura_api_key
   ```
4. Run the main script: `python main.py`

## Project Structure

- `config/`: Configuration settings
- `data_sources/`: API integrations (currently Oura Ring)
- `database/`: Database models and management
- `utils/`: Utility functions for data processing
- `main.py`: Main execution script

## Future Plans

- Integration with Google Sheets for additional metrics
- Data visualization dashboard
- Trend analysis and insights generation
