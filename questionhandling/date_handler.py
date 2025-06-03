from datetime import datetime, date, timedelta
from dateutil import parser as date_parser


class DateHandler:
    @staticmethod
    def parse_date(date_str: str, reference_date: date = None) -> date:
        if not date_str:
            return None
            
        if not reference_date:
            reference_date = date.today()
        
        try:
            parsed_date = date_parser.parse(date_str, fuzzy=True, default=datetime.combine(reference_date, datetime.min.time()))
            if parsed_date.date() < reference_date:
                if parsed_date.month < reference_date.month or (parsed_date.month == reference_date.month and parsed_date.day <= reference_date.day):
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1)
            return parsed_date.date()
        except:
            return None

    @staticmethod
    def format_date(date_obj: date) -> str:
        return date_obj.isoformat()

    @staticmethod
    def calculate_duration(duration_str: str, reference_date: date = None) -> int:
        if not duration_str:
            return 0
            
        if not reference_date:
            reference_date = date.today()
        
        duration_str = duration_str.lower().strip()
        
        # Handle "for a week", "for a month" etc.
        if duration_str.startswith('for a '):
            duration_str = '1 ' + duration_str[6:]
        elif duration_str.startswith('for '):
            duration_str = duration_str[4:]
        
        try:
            parts = duration_str.split()
            if len(parts) != 2:
                return 0
            
            number = int(parts[0])
            unit = parts[1].rstrip('s')
            
            if unit == 'day':
                return number
            elif unit == 'week':
                return number * 7
            elif unit == 'month':
                if reference_date.month == 12:
                    next_month = date(reference_date.year + 1, 1, 1)
                else:
                    next_month = date(reference_date.year, reference_date.month + 1, 1)
                last_day = (next_month - timedelta(days=1)).day
                return last_day
            elif unit == 'year':
                if reference_date.year % 4 == 0 and (reference_date.year % 100 != 0 or reference_date.year % 400 == 0):
                    return 366
                return 365
        except (ValueError, IndexError):
            pass
        
        return 0 