import os
from agents import Agent
from graph.state import PlannerState
from tools import plan_flight
from services import CityToAirportService, FlightService
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from questionhandling import QuestionGenerator, InputValidator

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
    self.question_generator = QuestionGenerator()
    self.input_validator = InputValidator()

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
    
    if response.get("status") == "no_flights":
      # Generate specific follow-up questions for no flights scenario
      follow_up_questions = self.question_generator.generate_no_flights_questions(user_data)
      
      # Use the first question if available, otherwise use a generic message
      if follow_up_questions:
        message = f"I couldn't find any flights from {user_data.departure_location} to {user_data.arrival_location} on {user_data.departure_date_leaving}. {follow_up_questions[0]}"
      else:
        message = f"I couldn't find any flights from {user_data.departure_location} to {user_data.arrival_location} on {user_data.departure_date_leaving}. Would you like to try a different date or destination?"
      
      state.messages.append(AIMessage(content=message))
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