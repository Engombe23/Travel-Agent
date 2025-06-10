from services import HotelService
from models import UserInput
from langchain.tools import tool
from dotenv import load_dotenv
import os
import json
import asyncio

load_dotenv()

@tool()
def plan_hotel(departure_location: str, arrival_location: str, adult_guests: str, departure_date_leaving: str, length_of_stay: str, holiday_type: str, arrival_date_coming_back: str) -> str:
    """
    Plans hotels using the HotelService class.
    """
    # Create UserInput with the provided parameters
    hotel_input = UserInput(
        departure_location=departure_location,
        arrival_location=arrival_location,
        adult_guests=adult_guests,
        departure_date_leaving=departure_date_leaving,
        length_of_stay=length_of_stay,
        holiday_type=holiday_type,
        arrival_date_coming_back=arrival_date_coming_back
    )

    # Get API key from environment
    rapid_api_key = os.environ.get("RAPIDAPIKEY")
    if not rapid_api_key:
        return json.dumps({"error": "RapidAPI key not found in environment variables"})

    # Call HotelService
    hotel_service = HotelService()
    try:
        # Run the async search_hotels method
        response = asyncio.run(hotel_service.search_hotels(input=hotel_input))
        return json.dumps(response, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})