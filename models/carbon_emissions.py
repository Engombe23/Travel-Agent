from pydantic import BaseModel

class CarbonEmissions(BaseModel):
  this_flight: int
  typical_for_this_route: int
  difference_percent: int