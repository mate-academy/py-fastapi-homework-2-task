from typing import List, Optional

from pydantic import BaseModel
from datetime import date

from database.models import MovieStatusEnum


class Country(BaseModel):
    id: int
    code: str
    name: str | None


class Genre(BaseModel):
    id: int
    name: str


class Actor(BaseModel):
    id: int
    name: str


class Language(BaseModel):
    id: int
    name: str


class Movie(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MoviesList(BaseModel):
    movies: list[Movie]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


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


class MovieUpdate(BaseModel):
    name: str = None
    date: date = None
    score: float = None
    overview: str = None
    status: MovieStatusEnum = None
    budget: float = None
    revenue: float = None
