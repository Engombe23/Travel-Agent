import requests
from typing import Dict, Any
from models import UserInput, Activity
from adapters.activity.base import ActivityAdapter
from datetime import datetime, timedelta

class TripAdvisorAdapter(ActivityAdapter):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "tripadvisor-com1.p.rapidapi.com"

    def _get_location_id(self, location: str) -> str:
        """Get the geoId for a location using auto-complete endpoint"""
        url = f"https://{self.base_url}/auto-complete"
        
        # Clean up location name
        location = location.strip()
        if not location:
            raise ValueError("Location name cannot be empty")
            
        # Try to extract city name if location contains additional details
        if "," in location:
            location = location.split(",")[0].strip()
        
        params = {
            "query": location
        }

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.base_url
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response_data = response.json()
            
            # Check if data array exists and is not empty
            if not response_data.get("data"):
                raise ValueError(f"No destination found for location: {location}")
            
            if not response_data["data"]:
                raise ValueError(f"Empty results for location: {location}")
            
            # Find the most relevant result
            for result in response_data["data"]:
                # Skip non-location results
                if result.get("__typename") != "AppPresentation_TypeaheadResult":
                    continue
                    
                # Get the location details
                tracking_items = result.get("trackingItems", {})
                place_type = tracking_items.get("placeType")
                
                # Prefer cities and regions
                if place_type in ["CITY", "REGION"]:
                    geo_id = result.get("geoId")
                    if geo_id:
                        return geo_id
            
            # If no specific city/region found, use the first result
            geo_id = response_data["data"][0].get("geoId")
            if not geo_id:
                raise ValueError(f"No valid geoId found for location: {location}")
                
            return geo_id
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to TripAdvisor API: {str(e)}")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Failed to get location ID: {str(e)}")

    def _get_activity_dates(self, input: UserInput) -> tuple[str, str]:
        """Determine activity start and end dates"""
        # Start activities the day after arrival
        start_date = datetime.strptime(input.departure_date_leaving, "%Y-%m-%d") + timedelta(days=1)
        # End activities the day before departure
        end_date = datetime.strptime(input.arrival_date_coming_back, "%Y-%m-%d") - timedelta(days=1)
        
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def search_activities(self, input: UserInput) -> Dict[str, Any]:
        """Search for activities using TripAdvisor API"""
        try:
            # Get location ID first
            geo_id = self._get_location_id(input.arrival_location)
            
            # Get activity dates
            start_date, end_date = self._get_activity_dates(input)
            
            url = f"https://{self.base_url}/attractions/search"

            params = {
                "geoId": geo_id,
                "startDate": start_date,
                "endDate": end_date,
                "adults": input.adult_guests,
                "language": "en",
                "currency": "GBP"
            }

            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.base_url
            }

            response = requests.get(url, headers=headers, params=params)
            activity_data = response.json()
            print("Raw TripAdvisor API response:", activity_data)
            
            # Check if we got a valid response
            if not activity_data.get("data"):
                return {"error": "Invalid response from TripAdvisor API"}
            
            attractions = activity_data.get("data", {}).get("attractions", [])
            if not attractions:
                return {"error": "No activities found"}

            activities = []
            for attraction in attractions:
                try:
                    # Extract contentId from the correct path
                    content_id = attraction.get("cardLink", {}).get("route", {}).get("params", {}).get("contentId")
                    
                    if not content_id:
                        continue
                        
                    # Map TripAdvisor fields to Activity model fields
                    # Extract image URLs as a list
                    image_url = attraction.get("cardPhoto", {}).get("sizes", {}).get("urlTemplate")
                    images = []
                    if image_url:
                        # Replace width and height placeholders with actual values
                        image_url = image_url.replace("{width}", "800").replace("{height}", "600")
                        # Ensure URL starts with https://
                        if not image_url.startswith(('http://', 'https://')):
                            image_url = f"https://{image_url}"
                        images.append(image_url)

                    # Extract price from merchandising text if available
                    price_text = attraction.get("merchandisingText", {}).get("htmlString", "")
                    price = None
                    if price_text and "from" in price_text.lower():
                        try:
                            price_amount = float(price_text.split("£")[1].strip())
                            price = {"amount": price_amount, "currency": "GBP"}
                        except (IndexError, ValueError):
                            pass

                    activity_data = {
                        "id": content_id,
                        "name": attraction.get("cardTitle", {}).get("string", ""),
                        "description": attraction.get("primaryInfo", {}).get("text", ""),
                        "category": attraction.get("primaryInfo", {}).get("text", ""),
                        "location": None,  # We'll get this from details endpoint
                        "price": price,
                        "reviews": {
                            "rating": attraction.get("bubbleRating", {}).get("rating"),
                            "count": attraction.get("bubbleRating", {}).get("numberReviews", {}).get("string", "0").replace("(", "").replace(")", "").replace(",", ""),
                            "provider": "TripAdvisor"
                        } if attraction.get("bubbleRating") else None,
                        "schedule": None,  # We'll get this from details endpoint
                        "booking_url": f"https://www.tripadvisor.com{attraction.get('cardLink', {}).get('route', {}).get('url', '')}",
                        "images": images,  # Pass the list of image URLs
                        "duration": None,  # We'll get this from details endpoint
                        "minimum_age": None,  # We'll get this from details endpoint
                        "maximum_age": None,  # We'll get this from details endpoint
                        "difficulty_level": None,  # We'll get this from details endpoint
                        "included_items": [],  # We'll get this from details endpoint
                        "excluded_items": [],  # We'll get this from details endpoint
                        "cancellation_policy": None,  # We'll get this from details endpoint
                        "languages": []  # We'll get this from details endpoint
                    }
                    
                    activity_obj = Activity.from_api(activity_data)
                    activities.append(activity_obj)
                except Exception as e:
                    print(f"Failed to parse activity: {str(e)}")
                    print(f"Activity data: {activity_data}")
                    continue  # Skip activities that can't be parsed

            if not activities:
                return {"error": "No activities could be parsed"}

            return {
                "status": "success",
                "results": activities
            }

        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to search activities: {str(e)}"}

    def get_activity_details(self, activity_id: str, input: UserInput) -> Dict[str, Any]:
        """Get detailed information about a specific activity"""
        try:
            # Get activity dates
            start_date, end_date = self._get_activity_dates(input)
            
            url = f"https://{self.base_url}/attractions/details"

            params = {
                "contentId": activity_id,
                "startDate": start_date,
                "endDate": end_date,
                "language": "en",
                "currency": "GBP"
            }

            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.base_url
            }

            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {"error": f"Failed to get activity details: {str(e)}"} 