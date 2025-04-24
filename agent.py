import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
from browser_use import Agent

load_dotenv()

# API key
api_key = os.environ.get("GEMINI_API_KEY")

def flight_date_info(date):
  date_format = '%d/%m/%Y'

  flight_date_obj = datetime.strptime(date, date_format)

  date_of_flight = flight_date_obj
  departure_date = date_of_flight.strftime(date_format)
  return departure_date

# Travel information
flight_date = input("What date are you flying? ")
date = flight_date_info(flight_date)

# Initial & final destinations
initial_destination = input("Where from? ")
final_destination = input("Where to? ")

flight_return_date = input(f"What date are you flying back to {initial_destination}? ")
return_date = flight_date_info(flight_return_date)

async def main():
  agent = Agent(
    task=f"Find the cheapest flight for a holiday from {initial_destination} to {final_destination} departing on {date} and returning on {return_date} on https://www.skyscanner.net/",
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)  
  )  
  await agent.run()

asyncio.run(main())