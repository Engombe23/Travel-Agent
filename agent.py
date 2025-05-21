import os
from agents.planner_agent import PlannerAgent
from models.user_input import UserInput
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")

user_input = UserInput(
    departure_location="LHR",
    arrival_location="CDG",
    adult_guests="1",
    departure_date_leaving="2025-09-15",
    length_of_stay="5",
    holiday_type="City Break",
    arrival_date_coming_back="2025-09-20"
)

agent = PlannerAgent(api_key)
result = agent.run(user_input)
print(result)