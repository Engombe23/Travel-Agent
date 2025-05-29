from abc import ABC, abstractmethod
from langchain_google_genai import ChatGoogleGenerativeAI

class Agent(ABC):

  def __init__(self, api_key: str):
    self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)

  @abstractmethod
  def run(self, input_data: dict) -> dict:
    pass