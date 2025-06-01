from models.hotel import Hotel, HotelDetails

class BookingAdapter:
  @staticmethod
  def to_hotel_model(data: dict) -> Hotel:
    return Hotel(
      details=HotelDetails(
        hotel_id=data["hotel_id"],
        name=data["hotel_name"],
        url=data["url"],
        arrivalDate=data["arrival_date"],
        departureDate=data["departure_date"],
        address=data["address"]
      )
    )