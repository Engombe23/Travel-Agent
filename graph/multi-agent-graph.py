from langgraph.graph import StateGraph, START, END
from graph.state import PlannerState
from agents import PlannerAgent, FlightAgent, HotelAgent, ActivityAgent
from services.holiday_package_service import HolidayPackageService

graph = StateGraph(PlannerState)

def planner_node(planner_agent: PlannerAgent):
  def node(state: PlannerState) -> PlannerState:
      message = state.messages[0] 
      return planner_agent.run(message)
  return node

def flight_node(flight_agent: FlightAgent):
  def node(state: PlannerState) -> PlannerState:
    return flight_agent.run(state)
  return node

def hotel_node(hotel_agent: HotelAgent):
  def node(state: PlannerState) -> PlannerState:
    return hotel_agent.run(state)
  return node

def activity_node(activity_agent: ActivityAgent):
  def node(state: PlannerState) -> PlannerState:
    return activity_agent.run(state)
  return node

def holiday_package_node(holiday_package_service: HolidayPackageService):
  def node(state: PlannerState) -> PlannerState:
    if state.flight and state.hotel and state.activities:
      package = holiday_package_service.create_package(
        name="Holiday Package",
        description="Your holiday package",
        outbound_flight=state.flight,
        inbound_flight=state.flight,  # Assuming same flight for simplicity
        hotel=state.hotel,
        activities=state.activities,
        start_date=state.user_input.departure_date_leaving,
        end_date=state.user_input.arrival_date_coming_back,
        number_of_guests=state.user_input.adult_guests,
        number_of_rooms=1,
        package_type="Standard"
      )
      state.holiday_package = package
    return state
  return node

graph.add_node("planner", planner_node)
graph.add_node("flight", flight_node)
graph.add_node("hotel", hotel_node)
graph.add_node("activity", activity_node)
graph.add_node("holiday_package", holiday_package_node)

graph.add_edge(START, "planner")
graph.add_edge("planner", "flight")
graph.add_edge("flight", "hotel")
graph.add_edge("hotel", "activity")
graph.add_edge("activity", "holiday_package")
graph.add_edge("holiday_package", END)

graph.compile()