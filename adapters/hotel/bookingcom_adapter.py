import requests
import json
from typing import Dict, Any
from models import UserInput
from adapters.hotel.base import HotelAdapter

class BookingAdapter(HotelAdapter):

  def __init__(self, api_key: str):
    super().__init__(api_key)
    self.base_url = "booking-com21.p.rapidapi.com"
    self.api_host = self.base_url

  def search_hotel_destination(self, input: UserInput) -> Dict[str, Any]:
    url = f"https://{self.base_url}/api/v1/hotels/searchDestination"

    params = {
      "query": input.arrival_location
    }

    headers = {
      "x-rapidapi-key": self.api_key,
      "x-rapidapi-host": self.api_host
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()

  def search_hotels(self, input: UserInput) -> Dict[str, Any]:
    url = f"https://{self.base_url}/api/v1/hotels/searchHotels"

    # Get dest_id from search_hotel_destination
    destination_response = self.search_hotel_destination(input)
    if not destination_response.get("data"):
        raise ValueError("No destination found")
    dest_id = destination_response["data"][0]["dest_id"]

    # Map holiday types to Booking.com search types
    search_type_mapping = {
        "city break": "city",
        "beach": "city",  # Beach locations are typically cities
        "ski": "city",    # Ski resorts are typically cities
        "countryside": "region",
        "mountain": "region",
        "lake": "region",
        "desert": "region",
        "island": "region",
        "wildlife": "region",
        "cultural": "city"
    }
    
    # Default to city if holiday type not found in mapping
    search_type = search_type_mapping.get(input.holiday_type.lower(), "city")

    params = {
      "dest_id": dest_id,
      "search_type": search_type,
      "arrival_date": input.departure_date_leaving,
      "departure_date": input.arrival_date_coming_back,
      "adults": input.adult_guests,
      "room_qty": input.adult_guests,
      "languagecode": "en-gb",
      "currency_code": "GBP"
    }

    headers = {
      "x-rapidapi-key": self.api_key,
      "x-rapidapi-host": self.api_host
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    # Get the raw hotel data
    hotels = data.get("data", {}).get("hotels", [])
    
    if not hotels:
        return []
        
    # Sort hotels by price
    sorted_hotels = sorted(
        hotels,
        key=lambda x: x.get("property", {}).get("priceBreakdown", {}).get("grossPrice", {}).get("value", float('inf'))
    )
    
    # Return the cheapest hotel
    return [sorted_hotels[0]]
  
  def get_hotel_details(self, input: UserInput) -> Dict[str, Any]:
    url = f"https://{self.base_url}/api/v1/hotels/getHotelDetails"

    # Get hotel_id from the first search result
    search_response = self.search_hotels(input)
    if not search_response.get("data"):
        raise ValueError("No hotels found")
    hotel_id = search_response["data"][0]["hotel_id"]

    params = {
      "hotel_id": hotel_id,
      "arrival_date": input.departure_date_leaving,
      "departure_date": input.arrival_date_coming_back,
      "adults": input.adult_guests,
      "languagecode": "en-gb",
      "currency_code": "GBP"
    }

    headers = {
      "x-rapidapi-key": self.api_key,
      "x-rapidapi-host": self.api_host
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()