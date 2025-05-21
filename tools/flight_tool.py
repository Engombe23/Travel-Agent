import subprocess
import json
from langchain.tools import tool

@tool()
def plan_flight(departure_location: str, arrival_location: str, departure_date_leaving: str, adult_guests: str, length_of_stay: str, holiday_type: str, arrival_date_coming_back: str) -> dict:
  """Plans a flight using the JS-based external API tool."""

  args = [
    "node", "api-index.js",
    f"--departure_location={departure_location}",
    f"--arrival_location={arrival_location}",
    f"--departure_date_leaving={departure_date_leaving}",
    f"--adult_guests={adult_guests}",
    f"--length_of_stay={length_of_stay}",
    f"--holiday_type={holiday_type}",
    f"--arrival_date_coming_back={arrival_date_coming_back}",
    "--cli"
  ]

  print("🚀 Running:", " ".join(args))

  try:
    result = subprocess.run(
      args,
      capture_output=True,
      encoding="utf-8",
      errors="replace",
      check=True
    )

    data = json.loads(result.stdout)
    return data
  except Exception as e:
    return {"error": f"Flight tool failed: {str(e)}"}
