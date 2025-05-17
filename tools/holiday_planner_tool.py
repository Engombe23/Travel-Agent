import subprocess
import json
from langchain.tools import tool

@tool
def plan_holiday() -> dict:
  """Plans a holiday using the JS-based external API tool."""
  try:
    result = subprocess.run(
      ["node", "api-index.js", "--cli"],
      capture_output=True,
      encoding="utf-8",
      errors="replace",
      check=True
    )
    data = json.loads(result.stdout)
    print("🧳 Holiday data:\n", json.dumps(data, indent=2))
    return data
  except subprocess.CalledProcessError as e:
    return {"error": f"Script failed: {e.stderr}"}
  except json.JSONDecodeError as e:
    return {"error": "Failed to parse JSON from JS output"}