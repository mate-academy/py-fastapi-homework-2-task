import datetime
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, field_validator

from database.models import MovieStatusEnum


class Movie(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class Genre(BaseModel):
    id: int
    name: str


class Actor(BaseModel):
    id: int
    name: str


class Language(BaseModel):
    id: int
    name: str


class Country(BaseModel):
    id: int
    code: str
    name: str | None


class ReadMoviesList(BaseModel):
    movies: List[Movie]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class ReadMovieDetail(Movie):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Country
    genres: List[Genre]
    actors: List[Actor]
    languages: List[Language]


class MovieCreate(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if len(value) > 255:
            raise ValueError("Movie name must be at most 255 characters")
        return value

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        if value.year > datetime.date.today().year + 1:
            raise ValueError("Movie date can't be more than one year in the future")
        return value

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("Movie score must be between 0 and 100")
        return value

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Movie budget must be greater than 0")
        return value

    @field_validator("revenue")
    @classmethod
    def validate_revenue(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Movie revenue must be greater than 0")
        return value


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("Movie score must be between 0 and 100")
        return value

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Movie budget must be greater than 0")
        return value

    @field_validator("revenue")
    @classmethod
    def validate_revenue(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Movie revenue must be greater than 0")
        return value
