from pydantic import BaseModel

class PriceBreakdown(BaseModel):
  outboundFlight: float
  inboundFlight: float
  hotel: float
  activity: float
  total: float

class Price(BaseModel):
  amount: float
  currency: str = "GBP"