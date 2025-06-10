from agents import Agent
from graph.state import PlannerState
from tools import plan_activity
from services import ActivityService
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

class ActivityAgent(Agent):

    def __init__(self, api_key: str):
        self.activity_service = ActivityService()
        super().__init__(api_key)
        
        self.agent = create_react_agent(
            tools=[plan_activity],
            model=self.llm
        )

    def run(self, state: PlannerState) -> PlannerState:
        user_data = state.user_input

        location = user_data.arrival_location

        # Create activity input with the correct location
        activity_input = user_data.model_copy(update={
            "arrival_location": location
        })

        try:
            response = self.activity_service.search_activities(activity_input)

            if response.get("error"):
                state.messages.append(AIMessage(content=f"Error searching activities: {response['error']}"))
                return state

            if not response.get("results"):
                state.messages.append(AIMessage(content="No suitable activities found."))
                return state

            # Select top 3 activities from the results
            state.activities = response["results"][:3]
            activity_names = [activity.name for activity in state.activities]
            state.messages.append(AIMessage(content=f"Activities successfully found: {', '.join(activity_names)}"))
        except Exception as e:
            state.messages.append(AIMessage(content=f"Failed to search or parse activity data: {str(e)}"))

        return state