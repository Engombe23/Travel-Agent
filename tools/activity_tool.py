from services import ActivityService
from models import UserInput
from langchain.tools import tool
from dotenv import load_dotenv
import os
import json

load_dotenv()

@tool()
def plan_activity(departure_location: str, arrival_location: str, adult_guests: str, departure_date_leaving: str, length_of_stay: str, holiday_type: str, arrival_date_coming_back: str) -> str:
    """
    Plans activities using the ActivityService class.
    """
    # Create UserInput with the provided parameters
    activity_input = UserInput(
        departure_location=departure_location,
        arrival_location=arrival_location,
        adult_guests=adult_guests,
        departure_date_leaving=departure_date_leaving,
        length_of_stay=length_of_stay,
        holiday_type=holiday_type,
        arrival_date_coming_back=arrival_date_coming_back
    )

    # Get API keys from environment
    rapid_api_key = os.environ.get("RAPIDAPIKEY")
    if not rapid_api_key:
        return json.dumps({"error": "RapidAPI key not found in environment variables"})

    # Call ActivityService with the adapter
    activity_service = ActivityService()
    response = activity_service.search_activities(activity_input)
    
    # Convert response to string
    return json.dumps(response, default=str)