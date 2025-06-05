from services import Service
from models import UserInput
from adapters.flight.serpaapi_adapter import SerpAPIAdapter

class FlightService(Service):

  def __init__(self, serp_api_key: str, base_url: str):
    self.adapter = SerpAPIAdapter(serp_api_key, base_url)

  def run(self, input: UserInput):
    try:
      outbound_result = self.adapter.search_flights(input, direction="outbound")
      if "error" in outbound_result:
        return outbound_result
      outbound_flight = outbound_result.get("flight")

      inbound_result = self.adapter.search_flights(input, direction="inbound")
      if "error" in inbound_result:
        return inbound_result
      inbound_flight = inbound_result.get("flight")
  
      outbound_price = outbound_flight.details.price
      inbound_price = inbound_flight.details.price
      
      total_amount = outbound_price.amount + inbound_price.amount
      total_price = f"{outbound_price.currency}{total_amount:.2f}"

      return {
        "status": "success",
        "flights": {
          "outbound": outbound_flight,
          "inbound": inbound_flight
        },
        "total_price": total_price
      }

    except Exception as e:
        return {"error": f"FlightService failed: {str(e)}"}