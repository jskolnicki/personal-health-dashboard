import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsAPI:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, service_account_file=None):
        """
        Initialize the Google Sheets API client using service account credentials.
        
        Args:
            service_account_file (str, optional): Path to service account JSON file.
                                                If None, uses the default path.
        """
        if service_account_file is None:
            # Default to looking in the same directory as this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            service_account_file = os.path.join(current_dir, 'sheets-credentials.json')  # Updated filename
        
        self.creds = Credentials.from_service_account_file(
            service_account_file, 
            scopes=self.SCOPES
        )
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_sheet_data(self, spreadsheet_id, range_name):
        """
        Retrieve data from Google Sheets.
        """
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range_name).execute()
        return result.get('values', [])