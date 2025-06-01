from models.hotel import Hotel, HotelDetails

class TripAdvisorAdapter:
  @staticmethod
  def to_hotel_model(data: dict) -> Hotel:
    return Hotel(
      details=HotelDetails(
        
      )
    )