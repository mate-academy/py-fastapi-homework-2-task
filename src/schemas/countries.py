from typing import List
from pydantic import BaseModel
from src.schemas.movies import MovieDetail


class CountryBase(BaseModel):
    name: str


class CountryCreate(CountryBase):
    pass


class CountryUpdate(CountryBase):
    pass


class CountryRead(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True
