from typing import Optional

from pydantic import BaseModel


class CountrySchema(BaseModel):
    name: Optional[str]


class CountryDetailSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        from_attributes = True
