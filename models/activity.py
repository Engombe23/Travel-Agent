from pydantic import BaseModel

class Activity(BaseModel):
  productId: str
  title: str
  productSlug: str