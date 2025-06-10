from typing import Dict, Any
import os
from models import UserInput
from adapters.activity.tripadvisor_adapter import TripAdvisorAdapter
from services.base import Service

class ActivityService(Service):
    def __init__(self):
        super().__init__()
        self.rapid_api_key = os.getenv("RAPIDAPIKEY")
        if not self.rapid_api_key:
            raise ValueError("RAPIDAPIKEY not found in environment variables")
            
        # Initialize adapters
        self.tripadvisor_adapter = TripAdvisorAdapter(self.rapid_api_key)

    def search_activities(self, input: UserInput) -> Dict[str, Any]:
        """Search for activities using available adapters"""
        try:
            # Try TripAdvisor first
            response = self.tripadvisor_adapter.search_activities(input)
            
            # If TripAdvisor fails or returns no results
            if response.get("error") or not response.get("results"):
                return {"Try a new adapater"}
            
            return response

        except Exception as e:
            return {"error": f"Failed to search activities: {str(e)}"}

    def get_activity_details(self, activity_id: str, input: UserInput) -> Dict[str, Any]:
        """Get detailed information about a specific activity"""
        try:
            # Try TripAdvisor first
            response = self.tripadvisor_adapter.get_activity_details(activity_id, input)
            
            # If TripAdvisor fails
            if response.get("error"):
                return {"error": "TripAdvisor failed"}
            
            return response

        except Exception as e:
            return {"error": f"Failed to get activity details: {str(e)}"}