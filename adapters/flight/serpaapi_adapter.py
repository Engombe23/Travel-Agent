import requests
import json
from typing import Dict, Any
from models import UserInput, Flight
from adapters.flight.base import FlightAdapter

class SerpAPIAdapter(FlightAdapter):

  def __init__(self, api_key: str, base_url: str):
    super().__init__(api_key, base_url)

  def search_flights(self, input: UserInput, direction: str = "outbound") -> Dict[str, Any]:
    if direction == "outbound":
      departure_id = input.departure_location
      arrival_id = input.arrival_location
      date = input.departure_date_leaving
    else:
      departure_id = input.arrival_location
      arrival_id = input.departure_location
      date = input.arrival_date_coming_back
    
    params = {
      "engine": "google_flights",
      "adults": input.adult_guests,
      "currency": "GBP",
      "hl": "en",
      "stops": "1",
      "departure_id": departure_id,
      "arrival_id": arrival_id,
      "outbound_date": date,
      "type": "2",
      "api_key": self.api_key
    }

    try:
      response = requests.get(self.base_url, params=params)
      data = response.json()

      if "error" in data:
        return {"error": f"SerpAPI error: {data['error']}"}
      
      # Check if no flights are found
      if not data.get("best_flights") and not data.get("other_flights"):
        return {
          "status": "no_flights",
          "message": f"No flights found for {departure_id} to {arrival_id} on {date}"
        }
      
      # Try to get flight data from either best_flights or other_flights
      best_flight = None
      if "best_flights" in data and data["best_flights"]:
        best_flight = data["best_flights"][0]
      elif "other_flights" in data and data["other_flights"]:
        best_flight = data["other_flights"][0]
      
      if not best_flight:
        return {"error": f"No flight data found in response: {json.dumps(data)}"}

      flight_url = data.get("search_metadata", {}).get("google_flights_url", "")
      flight = Flight.from_api(best_flight, flight_url)

      return {
        "status": "success",
        "flight": flight,
      }

    except Exception as e:
      return {"error": f"SerpAPIAdapter failed: {str(e)}"}