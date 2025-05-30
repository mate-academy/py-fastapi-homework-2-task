from starlette.config import Config

from database.models import MovieStatusEnum

from pydantic import BaseModel, Field, ConfigDict
from pydantic_extra_types.country import CountryAlpha2

from typing import List
from datetime import date



class MovieCreateBaseSchem(BaseModel):
    name: str
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryAlpha2
    genres: List[str]
    actors: List[str]
    languages: List[str]


class CountrySchem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str | None


class GenreSchem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorSchem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageSchem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieOut(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchem
    genres: List[GenreSchem]
    actors: List[ActorSchem]
    languages: List[LanguageSchem]

    class Config:
        orm_mode = True
