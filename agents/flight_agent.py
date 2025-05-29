from agents.base import Agent
from models.user_input import UserInput
from tools.flight_tool import plan_flight
from services.airport_lookup import CityToAirportService
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent


class FlightAgent(Agent):
  
  def __init__(self, api_key: str):
    super().__init__(api_key)
    self.agent = create_react_agent(
      tools=[plan_flight],
      model=self.llm
    )
  
  def run(self, input_data: UserInput) -> dict:
    # Convert city names to IATA codes
    self.lookup = CityToAirportService("data/airports.dat")
    
    # Get IATA codes for the cities
    departure_iata = self.lookup.find_first_iata_by_city(input_data.departure_location, "united kingdom")
    arrival_iata = self.lookup.find_first_iata_by_city(input_data.arrival_location, "france")

    if not departure_iata or not arrival_iata:
        return {"error": "Could not find IATA codes for one or both cities"}

    tool_msg = (
        f"Use these IATA codes: {departure_iata} for {input_data.departure_location} "
        f"and {arrival_iata} for {input_data.arrival_location}. "
        f"Plan a flight from {departure_iata} to {arrival_iata} "
        f"on {input_data.departure_date_leaving} "
        f"for {input_data.adult_guests} passenger(s) "
        f"staying for {input_data.length_of_stay} "
        f"for a {input_data.holiday_type} "
        f"and will come back on {input_data.arrival_date_coming_back}."
    )

    response = self.agent.invoke({"messages": [HumanMessage(content=tool_msg)]})
    return response