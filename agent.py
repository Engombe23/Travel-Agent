import os
from agents.planner_agent import PlannerAgent
from agents.flight_agent import FlightAgent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")

message = HumanMessage(
    content=(
        "Plan a trip for 4 adults from London to Paris starting from 2025-09-15 for 4 days with a few activities"
    )
)

planner_agent = PlannerAgent(api_key)
state = planner_agent.run(message)

flight_agent = FlightAgent(api_key)
state = flight_agent.run(state)

print("\n🎯 Final Planner State (with Flight):")
print(state)
print("\n🛫 Flight Details:")
print(state.flight)