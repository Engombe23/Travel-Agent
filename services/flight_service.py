from services.base import Service
from models.user_input import UserInput
from models.flight import Flight
import requests
import json

class FlightService(Service):

  def __init__(self, serp_api_key: str):
    self.api_key = serp_api_key

  def run(self, input: UserInput):
    base_url = "https://serpapi.com/search.json"
    
    common_params = {
      "engine": "google_flights",
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
      outbound_response = requests.get(base_url, params=outbound_params)
      outbound = outbound_response.json()
      
      # Check for API errors
      if "error" in outbound:
        return {"error": f"SerpAPI error: {outbound['error']}"}
      
      # Check if we have flight data
      if "best_flights" not in outbound:
        return {"error": f"Unexpected API response structure: {json.dumps(outbound)}"}
      
      best_outbound_flight = outbound.get("best_flights", [{}])[0]
      outbound_flight_url = outbound.get("search_metadata", {}).get("google_flights_url", "")
      
      outbound_flight = Flight.from_api(best_outbound_flight, outbound_flight_url)

      # Inbound Flights
      inbound_response = requests.get(base_url, params=inbound_params)
      inbound = inbound_response.json()
      
      # Check for API errors
      if "error" in inbound:
        return {"error": f"SerpAPI error: {inbound['error']}"}
      
      # Check if we have flight data
      if "best_flights" not in inbound:
        return {"error": f"Unexpected API response structure: {json.dumps(inbound)}"}
      
      best_inbound_flight = inbound.get("best_flights", [{}])[0]
      inbound_flight_url = inbound.get("search_metadata", {}).get("google_flights_url", "")

      inbound_flight = Flight.from_api(best_inbound_flight, inbound_flight_url)

      return {
        "status": "success",
        "flights": {
          "outbound": {
            "airline": outbound_flight.airline,
            "departure": {
              "airport": outbound_flight.departure_airport,
              "time": outbound_flight.departure_time
            },
            "arrival": {
              "airport": outbound_flight.arrival_airport,
              "time": outbound_flight.arrival_time
            },
            "duration": outbound_flight.duration,
            "price": outbound_flight.price,
            "booking_url": outbound_flight_url
          },
          "inbound": {
            "airline": inbound_flight.airline,
            "departure": {
              "airport": inbound_flight.departure_airport,
              "time": inbound_flight.departure_time
            },
            "arrival": {
              "airport": inbound_flight.arrival_airport,
              "time": inbound_flight.arrival_time
            },
            "duration": inbound_flight.duration,
            "price": inbound_flight.price,
            "booking_url": inbound_flight_url
          }
        },
        "total_price": f"£{float(outbound_flight.price.replace('£', '')) + float(inbound_flight.price.replace('£', '')):.2f}"
      }

    except Exception as e:
      return {"error": f"FlightService failed: {str(e)}"}