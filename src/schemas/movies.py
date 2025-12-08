from datetime import date, timedelta
from typing import List

from pydantic import BaseModel, ConfigDict, field_validator, Field


class MovieForList(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    movies: List[MovieForList]
    prev_page: str
    next_page: str
    total_pages: int
    total_items: int


class CountryRead(BaseModel):
    id: int
    code: str
    name: str | None
    model_config = ConfigDict(from_attributes=True)


class RelatedName(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=3, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetail(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryRead
    genres: list[RelatedName]
    actors: list[RelatedName]
    languages: list[RelatedName]
    model_config = ConfigDict(from_attributes=True)


class MovieUpdate(BaseModel):
    name: str | None = None
    date: date | None = None
    score: float | None = None
    overview: str | None = None
    status: str | None = None
    budget: float | None = None
    revenue: float | None = None
