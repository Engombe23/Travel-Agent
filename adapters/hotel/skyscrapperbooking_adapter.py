import requests
import json
from typing import Dict, Any
from models import UserInput, Hotel
from adapters.hotel.base import HotelAdapter

class SkyScrapperBookingAdapter(HotelAdapter):

  def __init__(self, api_key: str):
    super().__init__(api_key)
    self.base_url="https://sky-scrapper.p.rapidapi.com"

  def search_hotel_destination(self, input: UserInput) -> Dict[str, Any]:
    self.url = f"{self.base_url}/api/v1/hotels/searchDestinationOrHotel"

    params = {
      "query": input.arrival_location
    }

    headers = {
      "x-rapidapi-key": self.api_key,
      "x-rapidapi-host": self.url
    }

    response = requests.get(self.url, headers=headers, params=params)

    response_data = response.json()

    if not response_data.get("data", []):
      return {"error": "No destination or hotel existing!"}

    entity_id = response_data[0].get("entityId")

    if not entity_id:
      return {"error": "Entity ID not found in destination data"}

    return entity_id
  
  def search_hotels(self, input: UserInput, entity_id: str) -> Dict[str, Any]:
    self.url = f"{self.base_url}/api/v1/hotels/searchHotels"

    params = {
      "entityId": entity_id,
      "checkin": input.departure_date_leaving,
      "checkout": input.arrival_date_coming_back,
      "adults": input.adult_guests,
      "rooms": input.adult_guests,
      "currency": "GBP"
    }

    headers = {
      "x-rapidapi-key": self.api_key,
      "x-rapidapi-host": self.url
    }

    response = requests.get(self.url, headers=headers, params=params)

    data = response.json()

    raw_hotels_data = data.get("data", {}).get("hotels", [])

    if not raw_hotels_data:
      return {"error": "No hotels found"}
    
    hotels = []
    for hotel_data in raw_hotels_data:
      try: 
        hotel = Hotel.from_api(hotel_data)
        hotels.append(hotel)

        return hotel
      except Exception as e:
        return {"error": "Irregular hotel data: " + str(e)}


    return {
      "status": "success",
      "results": hotels
    }
  
  def get_hotel_details(self, hotel_id: str, entity_id: str) -> Dict[str, Any]:
    self.url = f"{self.base_url}/api/v1/hotels/getHotelDetails"

    params = {
      "hotelId": hotel_id,
      "entityId": entity_id,
      "currency": "GBP"
    }

    headers = {
      "x-rapidapi-key": self.api_key,
      "x-rapidapi-host": self.url
    }

    response = requests.get(self.url, headers=headers, params=params)

    return response.json()