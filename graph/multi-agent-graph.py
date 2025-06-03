from langgraph.graph import StateGraph, START, END
from graph.state import PlannerState
from agents import FlightAgent, PlannerAgent

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

graph.add_node("planner", planner_node)
graph.add_edge(START, "planner")
graph.add_edge("planner", "flight")
graph.add_edge("flight", END)

graph.compile()