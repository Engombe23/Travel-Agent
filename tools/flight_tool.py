from services.flight_service import FlightService
from models.user_input import UserInput
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

@tool()
def plan_flight(departure_location: str, arrival_location: str, adult_guests: str, departure_date_leaving: str, length_of_stay: str, holiday_type: str, arrival_date_coming_back: str):
 """
  Calls the Python FlightService to fetch flight details.
  """
 flight_input = UserInput(
  departure_location=departure_location,
  arrival_location=arrival_location,
  adult_guests=adult_guests,
  departure_date_leaving=departure_date_leaving,
  length_of_stay=length_of_stay,
  holiday_type=holiday_type,
  arrival_date_coming_back=arrival_date_coming_back,
 )

 service = FlightService(serp_api_key=os.environ.get("SERPAKEY"))
 result = service.run(flight_input)
 return result