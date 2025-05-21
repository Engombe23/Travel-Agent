from pydantic import BaseModel
from typing import Union

class PriceBreakdown(BaseModel):
  outboundFlight: float
  inboundFlight: float
  hotel: float
  activity: float
  total: float