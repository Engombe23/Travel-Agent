import os
from agents import Agent
from graph.state import PlannerState
from tools import plan_flight
from services import CityToAirportService, FlightService
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

class FlightAgent(Agent):
  
  def __init__(self, api_key: str):
    self.flight_service = FlightService(os.environ.get("SERPAKEY"), base_url="https://serpapi.com/search.json")
    super().__init__(api_key)
    
    self.lookup = CityToAirportService("data/airports.dat")
    self.agent = create_react_agent(
      tools=[plan_flight],
      model=self.llm
    )

  def run(self, state: PlannerState) -> PlannerState:
    user_data = state.user_input

    # City names to IATA codes
    departure_iata = self.lookup.find_first_iata_by_city(user_data.departure_location)
    arrival_iata = self.lookup.find_first_iata_by_city(user_data.arrival_location)

    if not departure_iata or not arrival_iata:
      state.messages.append(AIMessage(content="Could not find IATA codes for given cities."))
      return state
    
    # Create a new UserInput with IATA codes instead of city names for flight service
    flight_input = user_data.model_copy(update={
        "departure_location": departure_iata,
        "arrival_location": arrival_iata
    })

    response = self.flight_service.run(flight_input)

    if "error" in response:
       state.messages.append(AIMessage(content=f"Flight service error: {response['error']}")) 
       return state
    
    flights = response.get("flights", {})
    outbound_flight = flights.get("outbound")

    if not outbound_flight:
      state.messages.append(AIMessage(content="No outbound flight data found in service response."))
      return state
    
    try:
        state.flight = outbound_flight
        state.messages.append(AIMessage(content=f"Flight details successfully parsed."))
    except Exception as e:
        state.messages.append(AIMessage(content=f"Failed to parse flight data: {str(e)}"))
    
    return state