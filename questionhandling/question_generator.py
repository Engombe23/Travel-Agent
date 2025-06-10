from models.user_input import UserInput


class QuestionGenerator:
    @staticmethod
    def generate_follow_up_questions(user_input: UserInput) -> list[str]:
        questions = []
        
        # Check departure location - must be a specific place
        if (not user_input.departure_location or 
            user_input.departure_location.lower() in ['', 'unknown', 'anywhere', 'somewhere']):
            questions.append("Where would you like to depart from?")
        
        # Check arrival location - must be a specific place
        if (not user_input.arrival_location or 
            user_input.arrival_location.lower() in ['', 'unknown', 'anywhere', 'somewhere']):
            questions.append("Where would you like to go?")
        
        # Ask for number of guests unless:
        # 1. It was explicitly provided in the query
        # 2. It's a romantic/couple trip (2 adults)
        if (user_input.adult_guests <= 0 and 
            not any(word in user_input.holiday_type.lower() for word in ['romantic', 'couple', 'honeymoon'])):
            questions.append("How many adults will be traveling?")
        
        # Check dates - must be a specific date
        if not any(c.isdigit() for c in user_input.departure_date_leaving):
            questions.append("When would you like to depart? Please provide a specific date (e.g., 'July 10' or '10th July')")
        
        # Check length of stay - must be explicitly provided
        if user_input.length_of_stay <= 0:
            questions.append("How long would you like to stay?")
        
        # Check holiday type - must be specific
        if (not user_input.holiday_type or 
            user_input.holiday_type.lower() in ['', 'unknown', 'any', 'vacation', 'holiday']):
            questions.append("What type of holiday are you looking for? For example: beach vacation, city break, cultural tour, adventure, etc.")
        
        return questions 

    @staticmethod
    def generate_no_flights_questions(user_input: UserInput) -> list[str]:
        """Generate follow-up questions when no flights are found for the given input."""
        questions = []
        
        # If we have a specific date, suggest trying different dates
        if any(c.isdigit() for c in user_input.departure_date_leaving):
            questions.append("Would you like to try a different date? Please specify when you'd like to travel.")
        
        # If we have specific locations, suggest trying different destinations
        if (user_input.departure_location and user_input.arrival_location and
            user_input.departure_location.lower() not in ['', 'unknown', 'anywhere', 'somewhere'] and
            user_input.arrival_location.lower() not in ['', 'unknown', 'anywhere', 'somewhere']):
            questions.append("Would you like to try a different destination? Please specify where you'd like to go.")
        
        # If we don't have specific questions for dates or destinations, ask about flexibility
        if not questions:
            questions.append("Would you like to try a different date or destination? Please let me know what you'd prefer to change.")
        
        return questions 