from abc import ABC, abstractmethod
from models import UserInput
from typing import Dict, Any

class FlightAdapter(ABC):

  def __init__(self, api_key: str, base_url: str):
    self.api_key = api_key
    self.base_url = base_url

  @abstractmethod
  def search_flights(self, input: UserInput, direction: str = None) -> Dict[str, Any]:
    pass