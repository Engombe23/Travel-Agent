from abc import ABC, abstractmethod
from models import UserInput
from typing import Dict, Any

class HotelAdapter(ABC):

  def __init__(self, api_key: str):
    self.api_key = api_key

  @abstractmethod
  def search_hotel_destination(self, input: UserInput) -> Dict[str, Any]:
    pass
