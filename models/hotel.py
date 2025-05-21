from pydantic import BaseModel
from typing import List

class HotelDetails(BaseModel):
  ufi: int
  hotel_id: int
  name: str
  url: str
  arrivalDate: str
  departureDate: str


class Hotel(BaseModel):
  details: HotelDetails