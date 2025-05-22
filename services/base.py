from abc import ABC, abstractmethod

class Service(ABC):

  @abstractmethod
  def run(self, input_data: dict) -> dict:
    pass