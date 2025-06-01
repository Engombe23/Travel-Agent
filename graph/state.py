from pydantic import BaseModel
from typing import Optional, List
from models.user_input import UserInput
from models.flight import Flight
from models.hotel import Hotel
from models.activity import Activity
from langchain_core.messages.base import BaseMessage

class PlannerState(BaseModel):
  user_input: UserInput
  flight: Optional[Flight]
  hotel: Optional[Hotel]
  activity: Optional[Activity]
  messages: List[BaseMessage]