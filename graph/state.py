from pydantic import BaseModel
from typing import Optional, List
from models.user_input import UserInput
from models.flight import Flight
from models.hotel import Hotel
from models.activity import Activity
from models.holiday_package import HolidayPackage
from langchain_core.messages.base import BaseMessage

class PlannerState(BaseModel):
  user_input: UserInput
  flight: Optional[Flight]
  hotel: Optional[Hotel]
  activities: Optional[List[Activity]] = None
  holiday_package: Optional[HolidayPackage] = None
  messages: List[BaseMessage]