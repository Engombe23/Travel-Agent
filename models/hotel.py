from pydantic import BaseModel

class HotelDetails(BaseModel):
  hotel_id: int
  name: str
  url: str
  arrivalDate: str
  departureDate: str
  address: str


class Hotel(BaseModel):
  details: HotelDetails