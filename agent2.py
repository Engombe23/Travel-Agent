import os
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.holiday_planner_tool import plan_holiday
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
  model="gemini-2.0-flash", 
  temperature=0.5, 
  api_key=api_key
)

class HolidayPlannerResponse(BaseModel):
  itinerary: str

agent = create_react_agent(
  model=llm,
  tools=[plan_holiday],
  prompt="You are a helpful travel assistant. Use tools when appropriate to return detailed flight and hotel info.",
  response_format = HolidayPlannerResponse
)

response = agent.invoke(
  {"messages": [{"role": "user", "content": "Plan a 5-day city break from LHR to CDG for 1 person."}]}
)

response["structured_response"]
print("Agent Response: " + str(response))