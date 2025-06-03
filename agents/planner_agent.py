from agents import Agent, FlightAgent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from models import UserInput
from graph.state import PlannerState
from datetime import date, timedelta
from questionhandling import InputValidator, QuestionGenerator, DateHandler


class PlannerAgent(Agent):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.flight_agent = FlightAgent(api_key)
        self.parser = PydanticOutputParser(pydantic_object=UserInput)
        self.input_validator = InputValidator()
        self.question_generator = QuestionGenerator()
        self.date_handler = DateHandler()

    def run(self, message: HumanMessage) -> PlannerState:
        instructions = self._get_parser_instructions()
        prompt = HumanMessage(content=f"{message.content}\n{instructions}")
        
        response = self.llm.invoke([prompt])
        raw_data = self.parser.parse(response.content)
        
        # Check for follow-up questions BEFORE coercing the input
        follow_up_questions = self.question_generator.generate_follow_up_questions(raw_data)
        
        if follow_up_questions:
            return self._handle_follow_up_questions(message, raw_data, follow_up_questions)
        
        # Only coerce the input if we have all required information
        cleaned_input = self.input_validator.coerce_user_input(raw_data.model_dump())
        
        # Calculate return date if we have both departure date and length of stay
        if cleaned_input.departure_date_leaving and cleaned_input.length_of_stay > 0:
            departure_date = self.date_handler.parse_date(cleaned_input.departure_date_leaving)
            if departure_date:
                return_date = departure_date + timedelta(days=cleaned_input.length_of_stay)
                cleaned_input.arrival_date_coming_back = self.date_handler.format_date(return_date)
        
        return PlannerState(
            user_input=cleaned_input,
            messages=[message],
            flight=None,
            hotel=None,
            activity=None,
        )

    def _get_parser_instructions(self) -> str:
        return self.parser.get_format_instructions() + """
        IMPORTANT: You must ALWAYS return a valid JSON object with ALL of the following fields:
        - departure_location (string)
        - arrival_location (string)
        - adult_guests (integer)
        - departure_date_leaving (string)
        - length_of_stay (integer)
        - holiday_type (string)
        - arrival_date_coming_back (string)
        
        If a value is not mentioned in the user's query, set it to an empty string (for strings) or 0 (for integers).
        DO NOT use null or omit any fields. Every field must be present in the output JSON.
        
        Example output:
        {
          "departure_location": "London",
          "arrival_location": "Paris",
          "adult_guests": 2,
          "departure_date_leaving": "2024-07-10",
          "length_of_stay": 7,
          "holiday_type": "beach",
          "arrival_date_coming_back": "2024-07-17"
        }
        
        If the user says "I want to go on holiday from Birmingham to Paris on July 10th for 7 days", output:
        {
          "departure_location": "Birmingham",
          "arrival_location": "Paris",
          "adult_guests": 0,
          "departure_date_leaving": "July 10th",
          "length_of_stay": 7,
          "holiday_type": "",
          "arrival_date_coming_back": ""
        }
        """

    def _handle_follow_up_questions(self, message: HumanMessage, raw_data: UserInput, questions: list[str]) -> PlannerState:
        print("\nI need some more information to plan your trip:")
        for question in questions:
            print(f"\n{question}")
            user_response = input("> ").strip()
            self._update_input_based_on_question(raw_data, question, user_response)
        
        # Coerce the input after getting all responses
        cleaned_input = self.input_validator.coerce_user_input(raw_data.model_dump())
        
        # Calculate return date if we have both departure date and length of stay
        if cleaned_input.departure_date_leaving and cleaned_input.length_of_stay > 0:
            departure_date = self.date_handler.parse_date(cleaned_input.departure_date_leaving)
            if departure_date:
                return_date = departure_date + timedelta(days=cleaned_input.length_of_stay)
                cleaned_input.arrival_date_coming_back = self.date_handler.format_date(return_date)
        
        follow_up_message = AIMessage(
            content="Thank you for providing the additional information. I'll now plan your trip with these details."
        )
        return PlannerState(
            user_input=cleaned_input,
            messages=[message, follow_up_message],
            flight=None,
            hotel=None,
            activity=None,
        )

    def _update_input_based_on_question(self, cleaned_input: UserInput, question: str, response: str):
        if "depart from" in question.lower():
            cleaned_input.departure_location = response
        elif "go" in question.lower():
            cleaned_input.arrival_location = response
        elif "adults" in question.lower():
            try:
                cleaned_input.adult_guests = int(response)
            except ValueError:
                print("Please enter a number. Defaulting to 1 adult.")
                cleaned_input.adult_guests = 1
        elif "depart" in question.lower():
            parsed_date = self.date_handler.parse_date(response)
            if parsed_date:
                cleaned_input.departure_date_leaving = self.date_handler.format_date(parsed_date)
                if cleaned_input.length_of_stay > 0:
                    return_date = parsed_date + timedelta(days=cleaned_input.length_of_stay)
                    cleaned_input.arrival_date_coming_back = self.date_handler.format_date(return_date)
            else:
                print("Could not parse the date. Please use a format like 'July 10' or '10th July'")
        elif "stay" in question.lower():
            duration = self.date_handler.calculate_duration(response, 
                date.fromisoformat(cleaned_input.departure_date_leaving) 
                if cleaned_input.departure_date_leaving else None)
            if duration > 0:
                cleaned_input.length_of_stay = duration
            else:
                try:
                    cleaned_input.length_of_stay = int(response)
                except ValueError:
                    print("Please enter a number or duration (e.g., '7 days', '1 month'). Defaulting to 1 day.")
                    cleaned_input.length_of_stay = 1
            
            if cleaned_input.departure_date_leaving:
                departure = date.fromisoformat(cleaned_input.departure_date_leaving)
                return_date = departure + timedelta(days=cleaned_input.length_of_stay)
                cleaned_input.arrival_date_coming_back = self.date_handler.format_date(return_date)
        elif "holiday" in question.lower():
            cleaned_input.holiday_type = response