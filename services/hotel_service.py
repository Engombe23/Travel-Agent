from typing import List, Dict, Any
from models.hotel import Hotel
from services.base import Service
from adapters.hotel.bookingcom_adapter import BookingAdapter
from models import UserInput
import os

class HotelService(Service):
    def __init__(self):
        super().__init__()
        self.booking_adapter = BookingAdapter(api_key=os.getenv("RAPIDAPIKEY"))

    async def search_hotels(self, input: UserInput) -> List[Dict[str, Any]]:
        try:
            response = self.booking_adapter.search_hotels(input)
            return response  # response is already a list of hotels
        except Exception as e:
            print(f"Error searching hotels: {str(e)}")
            return []

    async def get_hotel_details(self, input: UserInput) -> Dict[str, Any]:
        try:
            return self.booking_adapter.get_hotel_details(input)
        except Exception as e:
            print(f"Error getting hotel details: {str(e)}")
            return {}
