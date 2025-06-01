import csv
from typing import List, Dict

class CityToAirportService:

  def __init__(self, csv_path: str):
    self.airports = self.__load_airports(csv_path)
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

  def __load_airports(self, path: str) -> List[Dict]:
    airports = []
    with open(path, encoding="utf-8") as file:
      reader = csv.reader(file)
      for row in reader:
        iata = row[4].strip()
        if iata and iata != "\\N":
          airports.append({
            "city": row[2].strip().lower(),
            "name": row[1].strip(),
            "country": row[3].strip().lower(),
            "iata": iata,
          })
    return airports
    
  def find_airports_by_city(self, city_name: str, country_name: str = None) -> List[Dict]:
    city_name = city_name.strip().lower()
    if country_name:
      country_name = country_name.strip().lower()
      return [airport for airport in self.airports 
              if airport["city"] == city_name and airport["country"] == country_name]
    return [airport for airport in self.airports if airport["city"] == city_name]

  def find_first_iata_by_city(self, city_name: str, country_name: str = None) -> str:
    city_key = city_name.strip().lower()
    
    # Check major airports first
    if city_key in self.major_airports:
        return self.major_airports[city_key]

    matches = self.find_airports_by_city(city_name, country_name)
    if not matches:
        return None

    # Prefer international airport
    for airport in matches:
        if "international" in airport["name"].lower():
            return airport["iata"]

    # Return first match if no international airport
    return matches[0]["iata"]

  def find_city_by_iata(self, iata_code: str) -> str:
    for airport in self.airports:
      if airport["iata"].upper() == iata_code.upper():
        return airport["city"]