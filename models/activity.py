from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from models.location import Location
from models.price import Price
from datetime import datetime, timedelta

class ActivityReview(BaseModel):
    rating: Optional[float] = Field(None, description="Activity rating out of 5")
    count: Optional[int] = Field(None, description="Number of reviews")
    provider: Optional[str] = Field(None, description="Review provider (e.g., TripAdvisor)")

class ActivityImage(BaseModel):
    url: HttpUrl
    description: Optional[str] = None

class ActivitySchedule(BaseModel):
    start_time: Optional[datetime] = Field(None, description="Activity start time")
    duration: Optional[timedelta] = Field(None, description="Activity duration")
    available_dates: Optional[List[datetime]] = Field(None, description="Available dates for booking")

class Activity(BaseModel):
    id: str = Field(..., description="Unique activity identifier")
    name: str = Field(..., description="Activity name")
    description: Optional[str] = Field(None, description="Activity description")
    category: Optional[str] = Field(None, description="Activity category (e.g., Museum, Tour, Adventure)")
    location: Optional[Location] = Field(None, description="Activity location")
    price: Optional[Price] = Field(None, description="Activity price")
    reviews: Optional[ActivityReview] = Field(None, description="Review information")
    schedule: Optional[ActivitySchedule] = Field(None, description="Activity schedule")
    booking_url: Optional[HttpUrl] = Field(None, description="URL to book the activity")
    images: Optional[List[ActivityImage]] = Field(None, description="Activity images")
    duration: Optional[timedelta] = Field(None, description="Typical duration of the activity")
    minimum_age: Optional[int] = Field(None, description="Minimum age requirement")
    maximum_age: Optional[int] = Field(None, description="Maximum age requirement")
    difficulty_level: Optional[str] = Field(None, description="Activity difficulty level")
    included_items: Optional[List[str]] = Field(None, description="Items included in the activity")
    excluded_items: Optional[List[str]] = Field(None, description="Items not included in the activity")
    cancellation_policy: Optional[str] = Field(None, description="Cancellation policy")
    languages: Optional[List[str]] = Field(None, description="Available languages for the activity")

    @property
    def activity_name(self) -> str:
        return self.name

    @property
    def activity_category(self) -> Optional[str]:
        return self.category

    @property
    def activity_duration(self) -> Optional[timedelta]:
        return self.duration

    @property
    def activity_price(self) -> Optional[Price]:
        return self.price

    @property
    def activity_description(self) -> Optional[str]:
        return self.description

    @property
    def activity_location(self) -> Optional[Location]:
        return self.location

    @property
    def activity_reviews(self) -> Optional[ActivityReview]:
        return self.reviews

    @property
    def activity_schedule(self) -> Optional[ActivitySchedule]:
        return self.schedule

    @property
    def activity_booking_url(self) -> Optional[HttpUrl]:
        return self.booking_url

    @property
    def activity_images(self) -> Optional[List[ActivityImage]]:
        return self.images

    @property
    def activity_minimum_age(self) -> Optional[int]:
        return self.minimum_age

    @property
    def activity_maximum_age(self) -> Optional[int]:
        return self.maximum_age

    @property
    def activity_difficulty_level(self) -> Optional[str]:
        return self.difficulty_level

    @property
    def activity_included_items(self) -> Optional[List[str]]:
        return self.included_items

    @property
    def activity_excluded_items(self) -> Optional[List[str]]:
        return self.excluded_items

    @property
    def activity_cancellation_policy(self) -> Optional[str]:
        return self.cancellation_policy

    @property
    def activity_languages(self) -> Optional[List[str]]:
        return self.languages
    @classmethod
    def from_api(cls, activity_data: dict) -> 'Activity':
        """Create an Activity instance from API response data"""
        # Extract images as a list of URLs from the activity_data dictionary
        images = activity_data.get("images", [])
        activity_images = []
        if isinstance(images, list):  # Only process if images is a list
            for image_url in images:
                if image_url:
                    try:
                        # Ensure the URL is properly formatted
                        if not image_url.startswith(('http://', 'https://')):
                            image_url = f"https://{image_url}"
                        activity_images.append(ActivityImage(url=image_url))
                    except Exception as e:
                        print(f"Failed to create ActivityImage from URL {image_url}: {str(e)}")
                        continue

        return cls(
            id=str(activity_data.get("id", "")),
            name=activity_data.get("name", ""),
            description=activity_data.get("description"),
            category=activity_data.get("category"),
            location=Location(
                latitude=activity_data.get("latitude"),
                longitude=activity_data.get("longitude")
            ) if activity_data.get("latitude") and activity_data.get("longitude") else None,
            price=Price(
                amount=activity_data.get("price", {}).get("amount"),
                currency=activity_data.get("price", {}).get("currency", "GBP")
            ) if activity_data.get("price") else None,
            reviews=ActivityReview(
                rating=activity_data.get("reviews", {}).get("rating"),
                count=activity_data.get("reviews", {}).get("count"),
                provider=activity_data.get("reviews", {}).get("provider")
            ) if activity_data.get("reviews") else None,
            schedule=ActivitySchedule(
                start_time=activity_data.get("start_time"),
                duration=timedelta(minutes=activity_data.get("duration_minutes", 0)),
                available_dates=activity_data.get("available_dates")
            ) if activity_data.get("start_time") else None,
            booking_url=activity_data.get("booking_url"),
            images=activity_images,
            duration=timedelta(minutes=activity_data.get("duration_minutes", 0)),
            minimum_age=activity_data.get("minimum_age"),
            maximum_age=activity_data.get("maximum_age"),
            difficulty_level=activity_data.get("difficulty_level"),
            included_items=activity_data.get("included_items", []),
            excluded_items=activity_data.get("excluded_items", []),
            cancellation_policy=activity_data.get("cancellation_policy"),
            languages=activity_data.get("languages", [])
        )
