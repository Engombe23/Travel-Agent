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

  @property
  def airline(self) -> Optional[str]:
      if self.details and self.details.flights:
          return self.details.flights[0].airline
      return None

  @property
  def departure_airport(self) -> Optional[AirportInfo]:
      # Prefer the top-level departureDetails if present
      if self.departureDetails:
          return self.departureDetails
      if self.details and self.details.flights:
          return self.details.flights[0].departure_airport
      return None

  @property
  def arrival_airport(self) -> Optional[AirportInfo]:
      # Prefer the top-level arrivalDetails if present
      if self.arrivalDetails:
          return self.arrivalDetails
      if self.details and self.details.flights:
          return self.details.flights[0].arrival_airport
      return None

  @property
  def duration(self) -> Optional[int]:
      if self.details:
          return self.details.total_duration
      if self.details and self.details.flights:
          return self.details.flights[0].duration
      return None

  @property
  def price_str(self) -> Optional[str]:
      # Return string representation of price (e.g. "£123.45")
      if self.details and self.details.price:
          return str(self.details.price)
      return None

  @property
  def price_float(self) -> Optional[float]:
      # Remove currency symbol and convert to float
      if self.details and self.details.price:
          price_str = str(self.details.price).replace('£', '').strip()
          try:
              return float(price_str)
          except ValueError:
              return None
      return None

  @property
  def departure_time(self) -> Optional[str]:
      if self.details and self.details.flights:
          # Assuming FlightSegment has departure_time attribute
          return getattr(self.details.flights[0], 'departure_time', None)
      return None

  @property
  def arrival_time(self) -> Optional[str]:
      if self.details and self.details.flights:
          # Assuming FlightSegment has arrival_time attribute
          return getattr(self.details.flights[0], 'arrival_time', None)
      return None

  @property
  def booking_url(self) -> str:
      return self.flightURL

  @classmethod
  def from_api(cls, flight: dict, metadata_url: str) -> "Flight":
    # Handle the case where flight data is in a different structure
    if "departure" in flight and "arrival" in flight:
        departure = flight["departure"]
        arrival = flight["arrival"]
        
        segment = FlightSegment(
            departure_airport=AirportInfo(
                name=departure["airport"].name,
                id=departure["airport"].id,
                time=departure.get("time")
            ),
            arrival_airport=AirportInfo(
                name=arrival["airport"].name,
                id=arrival["airport"].id,
                time=arrival.get("time")
            ),
            duration=flight.get("duration", 0),
            airplane=flight.get("airplane"),
            airline=flight.get("airline"),
            airline_logo=flight.get("airline_logo"),
            travel_class=flight.get("travel_class"),
            flight_number=flight.get("flight_number"),
            legroom=flight.get("legroom"),
            extensions=flight.get("extensions", [])
        )
        segments = [segment]
    else:
        segments = [
            FlightSegment(
                departure_airport=AirportInfo(
                    name=seg.get("departure_airport", {}).get("name", ""),
                    id=seg.get("departure_airport", {}).get("id", ""),
                    time=seg.get("departure_airport", {}).get("time", "")
                ),
                arrival_airport=AirportInfo(
                    name=seg.get("arrival_airport", {}).get("name", ""),
                    id=seg.get("arrival_airport", {}).get("id", ""),
                    time=seg.get("arrival_airport", {}).get("time", "")
                ),
                duration=seg.get("duration", 0),
                airplane=seg.get("airplane"),
                airline=seg.get("airline"),
                airline_logo=seg.get("airline_logo"),
                travel_class=seg.get("travel_class"),
                flight_number=seg.get("flight_number"),
                legroom=seg.get("legroom"),
                extensions=seg.get("extensions", [])
            )
            for seg in flight.get("flights", [])
        ]

    first_segment = segments[0] if segments else None

    flight_details = FlightDetails(
        flights=segments,
        total_duration=int(flight.get("total_duration", 0) or 0),
        carbon_emissions=CarbonEmissions(
          this_flight=flight.get("carbon_emissions", {}).get("this_flight", 0),
          typical_for_this_route=flight.get("carbon_emissions", {}).get("typical_for_this_route", 0),
          difference_percent=flight.get("carbon_emissions", {}).get("difference_percent", 0)
        ),
        price=Price(
            amount=flight.get("price", 0),
            currency=flight.get("currency", "GBP")
        ),
        type=flight.get("type", ""),
        airline_logo=flight.get("airline_logo", ""),
        extensions=flight.get("extensions", []),
        booking_token=flight.get("booking_token", "")
    )

    return cls(
        details=flight_details,
        departureDetails=first_segment.departure_airport if first_segment else AirportInfo(name="", id="", time=None),
        arrivalDetails=first_segment.arrival_airport if first_segment else AirportInfo(name="", id="", time=None),
        flightURL=metadata_url
    )
