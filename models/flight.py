from pydantic import BaseModel
from typing import Optional, List
from models.airport import AirportInfo
from models.carbon_emissions import CarbonEmissions
from models.price import PriceBreakdown

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
  price: PriceBreakdown
  type: Optional[str]
  airline_logo: Optional[str]
  extensions: Optional[List[str]]
  booking_token: Optional[str]

class Flight(BaseModel):
  details: FlightDetails
  departureDetails: AirportInfo
  arrivalDetails: AirportInfo
  flightURL: str
  price: PriceBreakdown