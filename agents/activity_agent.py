from agents import Agent
from tools import plan_activity
from langchain.agents import create_react_agent
from langgraph.prebuilt import create_react_agent
from models import Activity

class ActivityAgent(Agent):

  def __init__(self, api_key: str):
    super().__init__(api_key)
    self.agent = create_react_agent(
      tools=[plan_activity],
      model=self.llm
    )

  def run(self, activity: Activity) -> dict:
    user_msg = (
      f"Recommend activities based of flight and hotel information."
    )
