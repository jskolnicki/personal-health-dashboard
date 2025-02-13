import requests
from datetime import date, timedelta

class OuraAPI:
    BASE_URL = "https://api.ouraring.com/v2/usercollection"

    def __init__(self, access_token=None):
        """
        Initialize the Oura API client.
        
        Args:
            access_token (str, optional): Oura API access token.
                If not provided, it can be set later using set_access_token().
        """
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

    def set_access_token(self, access_token):
        """Set or update the access token."""
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def get_data(self, endpoint, start_date, end_date=None, **kwargs):
        if not self.access_token:
            raise ValueError("Access token not set. Please set it using set_access_token()")
            
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else start_date.isoformat()
        }
        params.update(kwargs)

        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()

    def get_sleep_data(self, start_date, end_date=None, **kwargs):
        return self.get_data("sleep", start_date, end_date, **kwargs)

    def get_daily_activity(self, start_date, end_date=None, **kwargs):
        return self.get_data("daily_activity", start_date, end_date, **kwargs)

    def get_daily_readiness(self, start_date, end_date=None, **kwargs):
        return self.get_data("daily_readiness", start_date, end_date, **kwargs)

    def get_daily_spo2(self, start_date, end_date=None, **kwargs):
        return self.get_data("daily_spo2", start_date, end_date, **kwargs)

    def get_tags(self, start_date, end_date=None, **kwargs):
        return self.get_data("tags", start_date, end_date, **kwargs)

    def get_workouts(self, start_date, end_date=None, **kwargs):
        return self.get_data("workout", start_date, end_date, **kwargs)

    def get_personal_info(self):
        return self.get_data("personal_info", date.today())

    def get_sessions(self, start_date, end_date=None, **kwargs):
        return self.get_data("session", start_date, end_date, **kwargs)