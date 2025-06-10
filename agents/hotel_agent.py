from agents import Agent
from graph.state import PlannerState
from tools import plan_hotel
from services import HotelService
from models.hotel import Hotel
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

class HotelAgent(Agent):
    def __init__(self, api_key: str):
        self.hotel_service = HotelService()
        super().__init__(api_key)
        
        self.agent = create_react_agent(
            tools=[plan_hotel],
            model=self.llm
        )

    async def run(self, state: PlannerState) -> PlannerState:
        user_data = state.user_input

        # Validate dates
        if user_data.departure_date_leaving >= user_data.arrival_date_coming_back:
            state.messages.append(AIMessage(content="Invalid dates: Check-out date must be after check-in date."))
            return state

        location = user_data.arrival_location

        # Use flight arrival location and dates for hotel search
        hotel_input = user_data.model_copy(update={
            "arrival_location": location,
            "check_in": user_data.departure_date_leaving,
            "check_out": user_data.arrival_date_coming_back
        })

        try:
            response = await self.hotel_service.search_hotels(
                input=hotel_input
            )

            if not response:
                state.messages.append(AIMessage(content="No suitable hotels found."))
                return state

            # Get the first (cheapest) hotel from the response
            hotel_data = response[0]
            state.hotel = Hotel.from_api(
                hotel_data=hotel_data,
                check_in=user_data.departure_date_leaving,
                check_out=user_data.arrival_date_coming_back
            )
            
            # Get the price information
            price = hotel_data.get("property", {}).get("priceBreakdown", {}).get("grossPrice", {})
            price_str = f"{price.get('value', 'N/A')} {price.get('currency', 'GBP')}"
            
            state.messages.append(AIMessage(content=f"Found the most affordable hotel: {state.hotel.name} at {price_str}"))
        except Exception as e:
            state.messages.append(AIMessage(content=f"Failed to search or parse hotel data: {str(e)}"))

        return state 