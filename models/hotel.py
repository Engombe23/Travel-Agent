from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from models.location import Location
from models.price import Price
from datetime import date

class HotelReview(BaseModel):
    rating: Optional[float] = Field(None, description="Hotel rating out of 10")
    count: Optional[int] = Field(None, description="Number of reviews")
    provider: Optional[str] = Field(None, description="Review provider (e.g., Booking.com)")

class HotelImage(BaseModel):
    url: HttpUrl
    description: Optional[str] = None

class HotelRoom(BaseModel):
    room_type: str = Field(..., description="Type of room (e.g., Standard, Deluxe)")
    beds: Optional[str] = Field(None, description="Bed configuration")
    capacity: Optional[int] = Field(None, description="Maximum number of guests")
    price: Optional[Price] = Field(None, description="Room price details")
    amenities: Optional[List[str]] = Field(None, description="Room-specific amenities")
    refundable: Optional[bool] = Field(None, description="Whether the booking is refundable")

class Hotel(BaseModel):
    id: str = Field(..., description="Unique hotel identifier")
    name: str = Field(..., description="Hotel name")
    entity_id: Optional[str] = Field(None, description="External system ID")
    address: Optional[str] = Field(None, description="Hotel address")
    location: Optional[Location] = Field(None, description="Geographic location")
    stars: Optional[int] = Field(None, description="Hotel star rating")
    reviews: Optional[HotelReview] = Field(None, description="Review information")
    check_in: Optional[date] = Field(None, description="Check-in date")
    check_out: Optional[date] = Field(None, description="Check-out date")
    amenities: Optional[List[str]] = Field(None, description="Hotel amenities")
    room: Optional[HotelRoom] = Field(None, description="Selected room details")
    booking_url: Optional[HttpUrl] = Field(None, description="URL to book the hotel")
    images: Optional[List[HotelImage]] = Field(None, description="Hotel images")
    total_price: Optional[Price] = Field(None, description="Total price for the stay")

    @property
    def hotel_name(self) -> str:
        return self.name

    @property
    def hotel_address(self) -> Optional[str]:
        return self.address

    @property
    def hotel_check_in(self) -> Optional[date]:
        return self.check_in

    @property
    def hotel_check_out(self) -> Optional[date]:
        return self.check_out

    @property
    def hotel_room(self) -> Optional[HotelRoom]:
        return self.room

    @property
    def hotel_total_price(self) -> Optional[Price]:
        return self.total_price

    @classmethod
    def from_api(cls, hotel_data: dict, check_in: Optional[date] = None, check_out: Optional[date] = None) -> 'Hotel':
        """Create a Hotel instance from API response data"""
        property_data = hotel_data.get("property", {})
        price_breakdown = property_data.get("priceBreakdown", {})
        gross_price = price_breakdown.get("grossPrice", {})
        
        # Extract address from accessibilityLabel
        accessibility_label = hotel_data.get("accessibilityLabel", "")
        address_parts = []
        if accessibility_label:
            # Split by newlines and look for address parts
            parts = accessibility_label.split("\n")
            for part in parts:
                if "arr." in part:  # Contains arrondissement
                    address_parts.append(part.strip())
                elif "km from centre" in part:  # Contains distance
                    address_parts.append(part.strip())
        
        # Extract room information from accessibilityLabel
        room_info = None
        if accessibility_label:
            for part in accessibility_label.split("\n"):
                if "beds" in part.lower():
                    room_info = part.strip()
                    break
        
        return cls(
            id=str(property_data.get("id", "")),
            name=property_data.get("name", ""),
            entity_id=str(hotel_data.get("hotel_id", "")),
            address=", ".join(address_parts) if address_parts else None,
            location=Location(
                lat=property_data.get("latitude"),
                lon=property_data.get("longitude")
            ) if property_data.get("latitude") and property_data.get("longitude") else None,
            stars=property_data.get("propertyClass"),
            reviews=HotelReview(
                rating=property_data.get("reviewScore"),
                count=property_data.get("reviewCount"),
                provider="Booking.com"
            ) if property_data.get("reviewScore") else None,
            check_in=check_in,
            check_out=check_out,
            amenities=property_data.get("amenities", []),
            room=HotelRoom(
                room_type=room_info or "Standard",
                beds=room_info,
                capacity=None,  # Not provided in API
                price=Price(
                    amount=gross_price.get("value"),
                    currency=gross_price.get("currency", "GBP")
                ) if gross_price else None,
                amenities=property_data.get("roomAmenities", []),
                refundable=any(badge.get("text", "").lower().startswith("free cancellation") 
                             for badge in price_breakdown.get("benefitBadges", []))
            ) if room_info or gross_price else None,
            booking_url=property_data.get("bookingUrl"),
            images=[HotelImage(url=url) for url in property_data.get("photoUrls", [])],
            total_price=Price(
                amount=gross_price.get("value"),
                currency=gross_price.get("currency", "GBP")
            ) if gross_price else None
        )