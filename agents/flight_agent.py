from agents.base import Agent
from models.user_input import UserInput
from tools.flight_tool import plan_flight
from langchain.agents import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent


class FlightAgent(Agent):
  
  def __init__(self, api_key: str):
    self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)
    self.agent = create_react_agent(
      tools=[plan_flight],
      model=self.llm
    )
  
  def run(self, input_data: UserInput) -> dict:
    user_msg = (
        f"Plan a flight from {input_data.departure_location} "
        f"to {input_data.arrival_location} on {input_data.departure_date_leaving} "
        f"for {input_data.adult_guests} passenger(s)"
        f"staying for {input_data.length_of_stay} "
        f"for a {input_data.holiday_type} "
        f"and will come back on {input_data.arrival_date_coming_back}."
    )
    response = self.agent.invoke({"messages": [HumanMessage(content=user_msg)]})
    return response
