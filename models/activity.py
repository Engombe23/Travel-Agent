from pydantic import BaseModel
from typing import List

class ActivityDetails(BaseModel):
  productId: str
  title: str
  cityName: str
  cityUfi: int
  countryCode: str
  productSlug: str
  taxonomySlug: str

class Activity(BaseModel):
  details: ActivityDetails