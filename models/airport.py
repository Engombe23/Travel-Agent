from pydantic import BaseModel
from typing import Optional

class AirportInfo(BaseModel):
  name: str
  id: str
  time: Optional[str]