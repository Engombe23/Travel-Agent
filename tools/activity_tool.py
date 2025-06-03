from services import ActivityService
from models import Activity, Price
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

@tool
def plan_activity(productId: str, title: str, productSlug: str, currency: Price):
  """
  Plans out activities 
  """
  activity_input = Activity(
    productId=productId,
    title=title,
    productSlug=productSlug
  )

  activity_currency = currency

  service = ActivityService(rapid_api_key=os.environ.get("RAPIDAPIKEY"))
  result = service.run(activity_input, activity_currency)
  return result