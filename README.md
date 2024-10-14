# Personal Health Analytics

This project aggregates and analyzes personal health data, primarily from the Oura Ring API, with plans to incorporate additional data sources in the future.

## Features

- Daily data retrieval from Oura Ring API
- Storage of sleep and nap data in a local MySQL database
- Modular design for easy integration of future data sources

## Setup

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
   python create_db.py
   ```
7. Run the main script (once it's developed):
   ```
   python main.py
   ```

## Project Structure

- `config/`: Configuration settings
- `data_sources/`: API integrations (currently Oura Ring)
  - `oura/`: Oura Ring API integration
    - `api.py`: Oura API client
    - `processing.py`: Data processing for Oura data
- `database/`: Database models and management
  - `models.py`: SQLAlchemy models for database tables
- `utils/`: Utility functions for data processing
- `create_db.py`: Script to set up the database
- `main.py`: Main execution script (to be developed)
- `.env`: Environment variables (not in version control)
- `requirements.txt`: Project dependencies

## Database Schema

The project currently uses two main tables:

1. `sleep_data`: Stores nightly sleep information
2. `nap_data`: Stores daytime nap information

Both tables include detailed sleep metrics such as sleep duration, sleep stages, heart rate, and HRV.

## Future Plans

- Implement data retrieval and processing from Oura API
- Develop main execution script
- Add data visualization capabilities
- Implement trend analysis and insights generation
- Integration with additional data sources

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.