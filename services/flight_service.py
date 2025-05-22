from services.base import Service
from models.user_input import UserInput
from models.flight import Flight
import requests

class FlightService(Service):

  def __init__(self, serp_api_key: str):
    self.api_key = serp_api_key

  def run(self, input: UserInput):
    base_url = "https://serpapi.com/search.json"
    
    common_params = {
      "engine": "google_flights",
      "departure_id": input.arrival_location,
      "adults": input.adult_guests,
      "currency": "GBP",
      "hl": "en",
      "gl": "uk",
      "stops": "1",
      "api_key": self.api_key,
    }

    outbound_params = {
      **common_params,
      "departure_id": input.departure_location,
      "arrival_id": input.arrival_location,
      "outbound_date": input.departure_date_leaving,
      "type": "2"
    }

    inbound_params = {
      **common_params,
      "departure_id": input.arrival_location,
      "arrival_id": input.departure_location,
      "outbound_date": input.arrival_date_coming_back,
      "type": "2"
    }

    try:
      # Outbound Flights
      outbound = requests.get(base_url, params=outbound_params).json()
      best_outbound_flight = outbound.get("best_flights", [{}])[0]
      outbound_flight_url = outbound.get("search_metadata", {}).get("google_flights_url", "")
      
      outbound_flight = Flight.from_api(best_outbound_flight, outbound_flight_url)

      inbound = requests.get(base_url, params=inbound_params).json()
      best_inbound_flight = inbound.get("best_flights", [{}])[0]
      inbound_flight_url = inbound.get("search_metadata", {}).get("google_flights_url", "")

      inbound_flight = Flight.from_api(best_inbound_flight, inbound_flight_url)


      return {
        "Outbound Flight": outbound_flight,
        "Inbound Flight":  inbound_flight
      }

    except Exception as e:
      return {"error": f"FlightService failed: {str(e)}"}