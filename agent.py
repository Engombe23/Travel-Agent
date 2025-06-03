import os
from agents import PlannerAgent, FlightAgent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")

initial_content = input("Please describe your trip: ")
message = HumanMessage(content=initial_content)

planner_agent = PlannerAgent(api_key)
state = planner_agent.run(message)

#flight_agent = FlightAgent(api_key)
#state = flight_agent.run(state)

print("\n🎯 Final Planner State (with user input):")
print(state)
#print("\n🛫 Flight Details:")
#print(state.flight)



