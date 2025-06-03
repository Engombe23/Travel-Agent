from pydantic import BaseModel, field_validator, model_validator, Field
from datetime import date, datetime
from dateutil import parser as date_parser

class UserInput(BaseModel):
    departure_location: str = Field(description="The city or location where the trip starts")
    arrival_location: str = Field(description="The destination city or location")
    adult_guests: int = Field(description="Number of adult guests")
    departure_date_leaving: str = Field(description="The departure date in YYYY-MM-DD format or natural language (e.g., 'in July', 'next month')")
    length_of_stay: int = Field(description="Number of days for the stay")
    holiday_type: str = Field(description="Type of holiday (e.g., Family Vacation, City Break)")
    arrival_date_coming_back: str = Field(description="The return date in YYYY-MM-DD format or natural language (e.g., 'in July', 'next month')")

    @field_validator("departure_date_leaving", "arrival_date_coming_back")
    def validate_date_format(cls, value: str) -> str:
        if not value:
            return value
            
        # First try to parse as ISO format
        try:
            parsed_date = date.fromisoformat(value)
            if parsed_date < date.today():
                raise ValueError("Date must be in the future.")
            return value
        except ValueError:
            # If not ISO format, try to parse as natural language
            try:
                # Use current year as reference
                parsed_date = date_parser.parse(value, fuzzy=True, default=datetime.combine(date.today(), datetime.min.time()))
                if parsed_date.date() < date.today():
                    # If the parsed date is in the past, try next year
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1)
                return parsed_date.date().isoformat()
            except:
                # If we can't parse it at all, return empty string
                return ""

    @model_validator(mode="after")
    def check_return_after_departure(self):
        # Only compare if both dates are in ISO format
        try:
            departure = date.fromisoformat(self.departure_date_leaving)
            arrival = date.fromisoformat(self.arrival_date_coming_back)
            if arrival <= departure:
                raise ValueError("Return date must be after departure date.")
        except ValueError:
            # If either date is not in ISO format, skip the comparison
            pass
        return self