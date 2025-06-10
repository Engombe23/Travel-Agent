import os
import asyncio
from agents import PlannerAgent, FlightAgent, HotelAgent, ActivityAgent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from typing import Tuple
from graph.state import PlannerState

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")

async def main():
    initial_content = input("Please describe your trip: ")
    message = HumanMessage(content=initial_content)

    # Initialize agents
    planner_agent = PlannerAgent(api_key)
    flight_agent = FlightAgent(api_key)
    hotel_agent = HotelAgent(api_key)
    activity_agent = ActivityAgent(api_key)

    # Run the planning workflow
    print("\n📝 Planning your trip...")
    state = planner_agent.run(message)

    print("\n✈️ Searching for flights...")
    state = flight_agent.run(state)

    print("\n🏨 Finding hotels...")
    state = await hotel_agent.run(state)

    print("\n🎯 Planning activities...")
    state = activity_agent.run(state)

    # Print final results
    print("\n🎉 Your Holiday Package:")
    print(f"Destination: {state.user_input.arrival_location}")
    print(f"Dates: {state.user_input.departure_date_leaving} to {state.user_input.arrival_date_coming_back}")
    print(f"Number of guests: {state.user_input.adult_guests}")

    if state.flight:
        print("\n✈️ Flight Details:")
        print(f"Airline: {state.flight.airline}")
        print(f"From: {state.flight.departure_airport.name} at {state.flight.departure_airport.time}")
        print(f"To: {state.flight.arrival_airport.name} at {state.flight.arrival_airport.time}")
        print(f"Price: {state.flight.price}")

    if state.hotel:
        print("\n🏨 Hotel Details:")
        print(f"Name: {state.hotel.hotel_name}")
        print(f"Address: {state.hotel.hotel_address}")
        print(f"Check-in: {state.hotel.hotel_check_in}")
        print(f"Check-out: {state.hotel.hotel_check_out}")
        print(f"Room: {state.hotel.hotel_room.room_type if state.hotel.hotel_room else 'Not specified'}")
        print(f"Price: {state.hotel.hotel_total_price.amount} {state.hotel.hotel_total_price.currency}")

    if state.activities:
        print("\n🎯 Activities:")
        for activity in state.activities:
            print(f"\n{activity.activity_name}")
            print(f"Category: {activity.activity_category}")
            print(f"Duration: {activity.activity_duration}")
            print(f"Price: {activity.activity_price.amount} {activity.activity_price.currency}")

    if state.holiday_package:
        print("\n🧳 Holiday Package Details:")
        print(f"Package Name: {state.holiday_package.name}")
        print(f"Description: {state.holiday_package.description}")
        print(f"Total Price: {state.holiday_package.total_price.amount} {state.holiday_package.total_price.currency}")
        print(f"Status: {state.holiday_package.status}")

    # Calculate total cost
    total_cost, currency = calculate_total_cost(state)
    print(f"\n💰 Total Package Cost: {format_price(total_cost, currency)}")

def calculate_total_cost(state: PlannerState) -> Tuple[float, str]:
    """Calculate total cost of the holiday package"""
    total_cost = 0
    currency = "GBP"  # Default currency
    
    # Add flight costs
    if state.flight and state.flight.price:
        total_cost += state.flight.price.amount
        currency = state.flight.price.currency
    
    # Add hotel cost
    if state.hotel and state.hotel.total_price:
        total_cost += state.hotel.total_price.amount
        currency = state.hotel.total_price.currency
    
    # Add activity costs
    if state.activities:
        for activity in state.activities:
            if activity.price:
                total_cost += activity.price.amount
                currency = activity.price.currency
    
    return total_cost, currency

def format_price(amount: float, currency: str) -> str:
    """Format price with currency symbol"""
    if currency == "GBP":
        return f"£{amount:.2f}"
    elif currency == "EUR":
        return f"€{amount:.2f}"
    elif currency == "USD":
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"

def format_holiday_summary(state: PlannerState) -> str:
    """Format the complete holiday package summary"""
    total_cost, currency = calculate_total_cost(state)
    
    summary = [
        "🎉 Your Holiday Package Summary 🎉",
        "\n✈️ Flight Details:",
        f"  • From: {state.flight.departure_airport.name if state.flight else 'Not selected'}",
        f"  • To: {state.flight.arrival_airport.name if state.flight else 'Not selected'}",
        f"  • Airline: {state.flight.airline if state.flight else 'Not selected'}",
        f"  • Price: {format_price(state.flight.price.amount, state.flight.price.currency) if state.flight and state.flight.price else 'Not selected'}"
    ]
    
    if state.hotel:
        summary.extend([
            "\n🏨 Hotel Details:",
            f"  • Name: {state.hotel.name}",
            f"  • Address: {state.hotel.address or 'Not specified'}",
            f"  • Check-in: {state.hotel.check_in}",
            f"  • Check-out: {state.hotel.check_out}",
            f"  • Room: {state.hotel.room.type if state.hotel.room else 'Not specified'}",
            f"  • Price: {format_price(state.hotel.total_price.amount, state.hotel.total_price.currency) if state.hotel.total_price else 'Not specified'}"
        ])
    
    if state.activities:
        summary.extend([
            "\n🎯 Activities:",
            *[f"  • {activity.name} - {format_price(activity.price.amount, activity.price.currency) if activity.price else 'Price not specified'}"
              for activity in state.activities]
        ])
    
    summary.extend([
        "\n💰 Total Cost:",
        f"  • {format_price(total_cost, currency)}"
    ])
    
    return "\n".join(summary)

if __name__ == "__main__":
    asyncio.run(main())