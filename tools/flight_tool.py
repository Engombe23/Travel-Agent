from services import FlightService
from models import UserInput
from services import CityToAirportService
from langchain.tools import tool
from dotenv import load_dotenv
import os
import json

load_dotenv()

airport_lookup = CityToAirportService("data/airports.dat")

@tool()
def get_iata_code(city_name: str) -> str:
 """
 Returns the IATA code for a given city and its airport.
 """
 code = airport_lookup.find_first_iata_by_city(city_name)
 if code:
  return code
 else:
  return f"No IATA code found for city: {city_name}"

@tool()
def plan_flight(departure_location: str, arrival_location: str, adult_guests: str, departure_date_leaving: str, length_of_stay: str, holiday_type: str, arrival_date_coming_back: str) -> str:
    """
    Plans flights using the FlightService class and a dataset of airports and cities.
    """
    # Create UserInput with the provided IATA codes
    flight_input = UserInput(
        departure_location=departure_location,
        arrival_location=arrival_location,
        adult_guests=adult_guests,
        departure_date_leaving=departure_date_leaving,
        length_of_stay=length_of_stay,
        holiday_type=holiday_type,
        arrival_date_coming_back=arrival_date_coming_back
    )

    # Get SerpAPI key from environment
    api_key = os.environ.get("SERPAKEY")
    if not api_key:
        return json.dumps({"error": "Serpa key not found in environment variables"})

    # SerpAPI Base URL
    base_url = "https://serpapi.com/search.json"

    # Call FlightService with IATA codes
    flight_service = FlightService(api_key, base_url)
    response = flight_service.run(flight_input)
    
    # Convert response to string
    return json.dumps(response, default=str)