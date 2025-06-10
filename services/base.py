from abc import ABC

class Service(ABC):

  def run(self, input_data: dict) -> dict:
    pass