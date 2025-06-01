from agents.base import Agent
from agents.flight_agent import FlightAgent
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from models.user_input import UserInput
from graph.state import PlannerState

class PlannerAgent(Agent):

  def __init__(self, api_key):
    super().__init__(api_key)
    self.flight_agent = FlightAgent(api_key)
    self.parser = PydanticOutputParser(pydantic_object=UserInput)

  def run(self, message: HumanMessage) -> PlannerState:

    # Using Natural Language to parse message into segments of the User Input model 
    # (Step 1 for building the multi-agent system)
    instructions = self.parser.get_format_instructions()
    prompt = HumanMessage(content=f"{message.content}\n{instructions}")  
   
    response = self.llm.invoke([prompt])
    parsed_input = self.parser.parse(response.content)

    return PlannerState(user_input=parsed_input, messages=[message], flight=None, hotel=None, activity=None)
    