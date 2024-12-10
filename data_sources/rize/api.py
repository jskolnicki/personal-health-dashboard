import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timezone
from utils.logging_config import setup_logging

logger = setup_logging()

class RizeAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.rize.io/api/v1/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query and return the response."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(self.base_url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                raise GraphQLError(data["errors"])
            
            return data["data"]
        except requests.exceptions.RequestException as e:
            raise RizeAPIError(f"Request failed: {str(e)}")

    def get_sessions(
        self,
        start_time: datetime,
        end_time: datetime,
        sort: str = "start_time"
    ) -> List[Dict[str, Any]]:
        """
        Get raw sessions data.
        
        Args:
            start_time (datetime): Start time for the query
            end_time (datetime): End time for the query
            sort (str): Sort field (default: "start_time")
            
        Returns:
            list: List of session records

        Example:
        query GetSessions {
            sessions(
                startTime: "2024-12-01T00:00:00Z"
                endTime: "2024-12-05T23:59:59Z"
            ) {
                id
                description
                createdAt
                startTime
                endTime
                title
                type
                source
            }
            }
        """
        query = """
        query GetSessions($startTime: ISO8601DateTime!, $endTime: ISO8601DateTime!, $sort: TimeEntrySortEnum!) {
            sessions(startTime: $startTime, endTime: $endTime, sort: $sort) {
                id
                description
                createdAt
                startTime
                endTime
                title
                type
                source
            }
        }
        """
        
        variables = {
            "startTime": start_time.astimezone(timezone.utc).isoformat(),
            "endTime": end_time.astimezone(timezone.utc).isoformat(),
            "sort": sort
        }
        
        result = self.execute_query(query, variables=variables)
        return result["sessions"]

    def get_summaries(
        self,
        start_date: date,
        end_date: date,
        bucket_size: str = "day"
    ) -> Dict[str, Any]:
        """
        Get raw time summaries data.
        
        Args:
            start_date (date): Start date
            end_date (date): End date
            bucket_size (str): Size of time buckets ('day', 'week', or 'month')
                
        Returns:
            dict: Raw summary data

        Example GraphQL query:
            query GetSummaries {
            summaries(
                startDate: "2024-12-01"
                endDate: "2024-12-05"
                bucketSize: "day"
                includeCategories: true
            ) {
                startTime
                endTime
                bucketSize
                focusTime
                focusTimeAverage
                breakTime
                breakTimeAverage
                meetingTime
                meetingTimeAverage
                trackedTime
                trackedTimeAverage
                workHours
                workHoursAverage
                buckets {
                startTime
                endTime
                focusTime
                breakTime
                meetingTime
                trackedTime
                workHours
                date
                wday
                dailyMeetingTimeAverage
                dailyTrackedTimeAverage
                dailyFocusTimeAverage
                dailyWorkHoursAverage
                }
            }
            }
        """
        query = """query GetSummaries($startDate: ISO8601Date!, $endDate: ISO8601Date!, $bucketSize: String!) {
        summaries(
            startDate: $startDate
            endDate: $endDate
            bucketSize: $bucketSize
            includeCategories: true
        ) {
            startTime
            endTime
            bucketSize
            focusTime
            focusTimeAverage
            breakTime
            breakTimeAverage
            meetingTime
            meetingTimeAverage
            trackedTime
            trackedTimeAverage
            workHours
            workHoursAverage
            buckets {
            startTime
            endTime
            focusTime
            breakTime
            meetingTime
            trackedTime
            workHours
            date
            wday
            dailyMeetingTimeAverage
            dailyTrackedTimeAverage
            dailyFocusTimeAverage
            dailyWorkHoursAverage
            }
        }
        }"""
        
        variables = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "bucketSize": bucket_size
        }
        
        result = self.execute_query(query, variables=variables)
        return result["summaries"]

class RizeAPIError(Exception):
    """Custom exception for Rize API errors"""
    pass

class GraphQLError(Exception):
    """Custom exception for GraphQL-specific errors"""
    def __init__(self, errors):
        self.errors = errors
        super().__init__(str(errors))