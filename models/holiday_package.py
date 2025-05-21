from pydantic import BaseModel
from typing import Optional
from models.user_input import UserInput
from models.flight import Flight
from models.hotel import Hotel
from models.activity import Activity
from models.price import PriceBreakdown

class HolidayPlanner(BaseModel):
  userInput: UserInput
  outboundFlight: Optional[Flight]
  inboundFlight: Optional[Flight]
  hotel: Optional[Hotel]
  activity: Optional[Activity]
  title: str
  subtitle: str
  priceBreakdown: PriceBreakdown
  formattedPrice: str