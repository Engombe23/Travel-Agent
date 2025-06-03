from datetime import date, timedelta
from models.user_input import UserInput
from .date_handler import DateHandler


class InputValidator:
    def __init__(self):
        self.date_handler = DateHandler()

    def coerce_user_input(self, user_input_dict: dict) -> UserInput:
        today = date.today()
        
        # Handle adult guests - only set default if explicitly provided
        guests = user_input_dict.get("adult_guests")
        if guests is not None:
            user_input_dict["adult_guests"] = self._coerce_guests(guests)
        
        # Handle departure date
        departure_date = self._coerce_departure_date(user_input_dict, today)
        
        # Handle length of stay - only set default if explicitly provided
        length_of_stay = user_input_dict.get("length_of_stay")
        if length_of_stay is not None:
            user_input_dict["length_of_stay"] = self._coerce_length_of_stay(length_of_stay, departure_date or today)
        
        # Calculate return date
        user_input_dict["arrival_date_coming_back"] = self._calculate_return_date(departure_date, user_input_dict.get("length_of_stay", 0))
        
        return UserInput(**user_input_dict)

    def _coerce_guests(self, guests) -> int:
        if guests is None or not str(guests).strip():
            return 0
        try:
            return int(guests)
        except (ValueError, TypeError):
            return 0

    def _coerce_departure_date(self, user_input_dict: dict, today: date) -> date:
        if user_input_dict.get("departure_date_leaving") and any(c.isdigit() for c in user_input_dict["departure_date_leaving"]):
            departure_date = self.date_handler.parse_date(user_input_dict["departure_date_leaving"], today)
            if departure_date:
                user_input_dict["departure_date_leaving"] = self.date_handler.format_date(departure_date)
                return departure_date
            user_input_dict["departure_date_leaving"] = ""
        return None

    def _coerce_length_of_stay(self, length_of_stay, reference_date: date) -> int:
        if isinstance(length_of_stay, str):
            duration = self.date_handler.calculate_duration(length_of_stay, reference_date)
            if duration > 0:
                return duration
            try:
                return int(''.join(filter(str.isdigit, length_of_stay)))
            except ValueError:
                return 0
        return int(length_of_stay) if length_of_stay else 0

    def _calculate_return_date(self, departure_date: date, length_of_stay: int) -> str:
        if departure_date and length_of_stay > 0:
            return_date = departure_date + timedelta(days=length_of_stay)
            return self.date_handler.format_date(return_date)
        return "" 