from abc import ABC, abstractmethod
from models import UserInput
from typing import Dict, Any

class ActivityAdapter(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def search_activities(self, input: UserInput) -> Dict[str, Any]:
        """Search for activities based on user input"""
        pass

    @abstractmethod
    def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific activity"""
        pass 