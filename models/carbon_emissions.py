from pydantic import BaseModel

class CarbonEmissions(BaseModel):
  this_flight: int
  typical_for_this_route: int
  different_percent: int