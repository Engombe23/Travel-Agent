from agents.flight_agent import FlightAgent

class PlannerAgent:

  def __init__(self, api_key):
    self.flight_agent = FlightAgent(api_key)

  def run(self, user_input: str) -> dict:
    flight_response = self.flight_agent.run(user_input)

    return {
      "flight": flight_response
    }
    