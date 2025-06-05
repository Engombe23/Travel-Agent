import csv
from typing import List, Dict

class CityToAirportService:
    """
    A service for looking up airport information by city name or IATA code.
    
    This service maintains a database of airports and provides methods to:
    - Find airports by city name
    - Look up IATA codes for cities
    - Find cities by IATA codes
    """

    def __init__(self, csv_path: str):
        """
        Initialize the service with airport data from a CSV file.
        
        Args:
            csv_path (str): Path to the CSV file containing airport data
        """
        self.airports = self.__load_airports(csv_path)
        # Create a lookup dictionary for IATA codes
        self.iata_to_city = {airport["iata"].upper(): airport["city"] for airport in self.airports}
        # Define major airports for common cities
        self.major_airports = {
          "london": "LHR",  # Heathrow
          "paris": "CDG",   # Charles de Gaulle
          "new york": "JFK",
          "tokyo": "HND",
          "dubai": "DXB",
          "rome": "FCO",
          "amsterdam": "AMS",
          "frankfurt": "FRA",
          "madrid": "MAD",
          "istanbul": "IST"
        }
        
        # Map alternative names to their actual city names
        self.alternative_names = {
            "bali": "denpasar",
            "birmingham": "birmingham",
            "manchester": "manchester",
            "edinburgh": "edinburgh",
            "glasgow": "glasgow",
            "barcelona": "barcelona",
            "milan": "milan",
            "munich": "munich",
            "berlin": "berlin",
            "vienna": "vienna",
            "prague": "prague",
            "budapest": "budapest",
            "warsaw": "warsaw",
            "athens": "athens",
            "lisbon": "lisbon",
            "dublin": "dublin",
            "copenhagen": "copenhagen",
            "oslo": "oslo",
            "stockholm": "stockholm",
            "helsinki": "helsinki"
        }

    def __load_airports(self, path: str) -> List[Dict]:
        """
        Load airport data from a CSV file.
        
        Args:
            path (str): Path to the CSV file
            
        Returns:
            List[Dict]: List of airport dictionaries containing city, name, country, and IATA code
            
        Raises:
            FileNotFoundError: If the CSV file cannot be found
            ValueError: If the CSV file is malformed or empty
        """
        airports = []
        try:
            with open(path, encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) < 5:
                        continue  # Skip malformed rows
                    iata = row[4].strip()
                    if iata and iata != "\\N":
                        airports.append({
                            "city": row[2].strip().lower(),
                            "name": row[1].strip(),
                            "country": row[3].strip().lower(),
                            "iata": iata,
                        })
            if not airports:
                raise ValueError("No valid airport data found in the CSV file")
            return airports
        except FileNotFoundError:
            raise FileNotFoundError(f"Airport data file not found: {path}")
        except Exception as e:
            raise ValueError(f"Error loading airport data: {str(e)}")
    
    def find_airports_by_city(self, city_name: str, country_name: str = None) -> List[Dict]:
        """
        Find all airports in a given city.
        
        Args:
            city_name (str): Name of the city to search for
            country_name (str, optional): Name of the country to filter by
            
        Returns:
            List[Dict]: List of matching airports with their details
        """
        city_name = city_name.strip().lower()
        # Check if the input is an alternative name
        if city_name in self.alternative_names:
            city_name = self.alternative_names[city_name]
            
        if country_name:
            country_name = country_name.strip().lower()
            return [airport for airport in self.airports 
                    if airport["city"] == city_name and airport["country"] == country_name]
        return [airport for airport in self.airports if airport["city"] == city_name]

    def find_first_iata_by_city(self, city_name: str, country_name: str = None) -> str:
        """
        Find the most appropriate IATA code for a city.
        
        This method implements a smart selection algorithm that:
        1. First checks if the city has a predefined major airport
        2. Then checks if the input is an alternative name
        3. Then searches the full database
        4. Prioritizes international airports when multiple options exist
        
        Args:
            city_name (str): Name of the city to search for
            country_name (str, optional): Name of the country to filter by
            
        Returns:
            str: The IATA code if found, None otherwise
        """
        city_key = city_name.strip().lower()
        
        # Check major airports first
        if city_key in self.major_airports:
            return self.major_airports[city_key]
            
        # Check alternative names
        if city_key in self.alternative_names:
            city_key = self.alternative_names[city_key]
            # Check if the mapped city is in major airports
            if city_key in self.major_airports:
                return self.major_airports[city_key]

        matches = self.find_airports_by_city(city_key, country_name)
        if not matches:
            return None

        # Prefer international airport
        for airport in matches:
            if "international" in airport["name"].lower():
                return airport["iata"]

        # Return first match if no international airport
        return matches[0]["iata"]

    def find_city_by_iata(self, iata_code: str) -> str:
        """
        Find a city name by its IATA airport code.
        
        Args:
            iata_code (str): The IATA airport code to look up
            
        Returns:
            str: The city name if found, None otherwise
        """
        if not iata_code or not isinstance(iata_code, str):
            return None
        
        iata_code = iata_code.strip().upper()
        if len(iata_code) != 3 or not iata_code.isalpha():
            return None
        
        return self.iata_to_city.get(iata_code)