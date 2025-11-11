from pydantic import BaseModel
from typing import Optional


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        from_attributes = True
