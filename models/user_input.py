from pydantic import BaseModel

class UserInput(BaseModel):
  departure_location: str
  arrival_location: str
  adult_guests: str
  departure_date_leaving: str
  length_of_stay: str
  holiday_type: str
  arrival_date_coming_back: str