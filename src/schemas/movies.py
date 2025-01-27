from typing import Optional

from pydantic import BaseModel
from datetime import date

from database.models import MovieStatusEnum


class MovieBase(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float

    class Config:
        from_attributes = True


class MovieCreate(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    class Config:
        from_attributes = True


class MovieUpdate(BaseModel):
    name: str
    date: str
    score: float
    overview: str
    status: str
    budget: float
    revenue: float


class MovieListPaginated(MovieBase):
    movies: list[MovieBase]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class Genre(BaseModel):
    name: str


class Actor(BaseModel):
    name: str


class Country(BaseModel):
    code: str
    name: str


class Language(BaseModel):
    name: str


class MovieDetail(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Country
    genres: list[Genre]
    actors: list[Actor]
    languages: list[Language]
