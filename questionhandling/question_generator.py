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