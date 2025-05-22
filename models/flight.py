from pydantic import BaseModel
from typing import Optional, List
from models.airport import AirportInfo
from models.carbon_emissions import CarbonEmissions
from models.price import Price

class FlightSegment(BaseModel):
  departure_airport: AirportInfo
  arrival_airport: AirportInfo
  duration: int
  airplane: Optional[str]
  airline: Optional[str]
  airline_logo: Optional[str]
  travel_class: Optional[str]
  flight_number: Optional[str]
  legroom: Optional[str]
  extensions: Optional[List[str]]

class FlightDetails(BaseModel):
  flights: List[FlightSegment]
  total_duration: int
  carbon_emissions: CarbonEmissions
  price: Price
  type: Optional[str]
  airline_logo: Optional[str]
  extensions: Optional[List[str]]
  booking_token: Optional[str]

class Flight(BaseModel):
  details: FlightDetails
  departureDetails: AirportInfo
  arrivalDetails: AirportInfo
  flightURL: str
  price: Price

  @classmethod
  def from_api(cls, flight: dict, metadata_url: str) -> "Flight":

    flight_details = FlightDetails(
      flights=[FlightSegment(**segment) for segment in flight["flights"]],
      total_duration=flight["total_duration"],
      carbon_emissions=CarbonEmissions(**flight["carbon_emissions"]),
      price=Price(amount=flight["price"]),
      type=flight.get("type"),
      airline_logo=flight.get("airline_logo"),
      extensions=flight.get("extensions"),
      booking_token=flight.get("booking_token")
    )

    return cls(
      details=flight_details,
      departureDetails=AirportInfo(**flight["flights"][0]["departure_airport"]),
      arrivalDetails=AirportInfo(**flight["flights"][0]["arrival_airport"]),
      flightURL=metadata_url,
      price=Price(amount=flight["price"])
    )