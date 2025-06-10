from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from models.flight import Flight
from models.hotel import Hotel
from models.activity import Activity
from models.price import Price

class HolidayPackage(BaseModel):
    id: str = Field(..., description="Unique package identifier")
    name: str = Field(..., description="Package name")
    description: Optional[str] = Field(None, description="Package description")
    outbound_flight: Optional[Flight] = Field(None, description="Outbound flight details")
    inbound_flight: Optional[Flight] = Field(None, description="Inbound flight details")
    hotel: Optional[Hotel] = Field(None, description="Hotel details")
    activities: Optional[List[Activity]] = Field(None, description="Selected activities")
    start_date: date = Field(..., description="Holiday start date")
    end_date: date = Field(..., description="Holiday end date")
    total_price: Price = Field(..., description="Total package price")
    number_of_guests: int = Field(..., description="Number of guests")
    number_of_rooms: int = Field(..., description="Number of hotel rooms")
    package_type: str = Field(..., description="Type of holiday package (e.g., City Break, Beach Holiday)")
    status: str = Field(..., description="Package status (e.g., Draft, Confirmed, Cancelled)")
    created_at: date = Field(..., description="Package creation date")
    updated_at: date = Field(..., description="Last update date")

    def calculate_total_price(self) -> Price:
        """Calculate the total price of the package"""
        total_amount = 0
        currency = "GBP"  # Default currency

        # Add flight prices
        if self.outbound_flight and self.outbound_flight.price:
            total_amount += self.outbound_flight.price.amount
            currency = self.outbound_flight.price.currency

        if self.inbound_flight and self.inbound_flight.price:
            total_amount += self.inbound_flight.price.amount
            currency = self.inbound_flight.price.currency

        # Add hotel price
        if self.hotel and self.hotel.total_price:
            total_amount += self.hotel.total_price.amount
            currency = self.hotel.total_price.currency

        # Add activity prices
        if self.activities:
            for activity in self.activities:
                if activity.price:
                    total_amount += activity.price.amount
                    currency = activity.price.currency

        return Price(amount=total_amount, currency=currency)

    def validate_package(self) -> bool:
        """Validate the package for completeness and consistency"""
        if not self.outbound_flight or not self.inbound_flight:
            return False

        if not self.hotel:
            return False

        if not self.activities:
            return False

        # Validate dates
        if self.start_date >= self.end_date:
            return False

        # Validate flight dates
        if (self.outbound_flight.departure_time.date() != self.start_date or
            self.inbound_flight.arrival_time.date() != self.end_date):
            return False

        # Validate hotel dates
        if (self.hotel.check_in != self.start_date or
            self.hotel.check_out != self.end_date):
            return False

        return True

    def generate_itinerary(self) -> str:
        """Generate a detailed itinerary for the holiday package"""
        itinerary = f"""
Holiday Package: {self.name}
Type: {self.package_type}
Duration: {self.start_date} to {self.end_date}
Number of Guests: {self.number_of_guests}
Number of Rooms: {self.number_of_rooms}

FLIGHTS:
Outbound: {self.outbound_flight.airline} {self.outbound_flight.flight_number}
         From: {self.outbound_flight.departure_airport} at {self.outbound_flight.departure_time}
         To: {self.outbound_flight.arrival_airport} at {self.outbound_flight.arrival_time}

Inbound: {self.inbound_flight.airline} {self.inbound_flight.flight_number}
        From: {self.inbound_flight.departure_airport} at {self.inbound_flight.departure_time}
        To: {self.inbound_flight.arrival_airport} at {self.inbound_flight.arrival_time}

HOTEL:
Name: {self.hotel.name}
Address: {self.hotel.address}
Check-in: {self.hotel.check_in}
Check-out: {self.hotel.check_out}
Room Type: {self.hotel.room.room_type if self.hotel.room else 'Not specified'}

ACTIVITIES:
"""
        for activity in self.activities:
            itinerary += f"""
{activity.name}
Category: {activity.category}
Duration: {activity.duration}
Price: {activity.price.amount} {activity.price.currency}
"""

        itinerary += f"""
TOTAL COST: {self.total_price.amount} {self.total_price.currency}
"""
        return itinerary