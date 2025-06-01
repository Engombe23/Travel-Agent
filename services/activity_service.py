from services.base import Service
from models.activity import Activity
from models.price import Price
import requests

class ActivityService(Service):

  def __init__(self, rapid_api_key: str):
    self.api_key = rapid_api_key

  def run(self, activity: Activity, price: Price):
    base_url = "booking-com.p.rapidapi.com"

    params = {
      "slug": activity.productSlug,
      "locale": "en-gb",
      "currency": price.currency,
      "api_key": self.api_key,
    }

    try:
      # Activity Details
      activity_response = requests.get(base_url, params).json()
      activity_name = activity_response.get("name", [{}])[0]
      
      return {
        "Activity Name": activity_name  
      }
    except Exception as e:
      return {"error": f"ActivityService failed: {str(e)}"}