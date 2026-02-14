import datetime
from enum import Enum
from typing import Optional, Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MovieStatus(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"


class MovieBase(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: "CountryOut"
    genres: list["NameOut"]
    actors: list["NameOut"]
    languages: list["NameOut"]

    model_config = ConfigDict(from_attributes=True)


class MovieDetail(MovieBase):
    pass


class MovieShort(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    movies: list[MovieShort]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class CountryOut(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class NameOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreateRequest(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatus
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieCreateResponse(MovieBase):
    pass


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
