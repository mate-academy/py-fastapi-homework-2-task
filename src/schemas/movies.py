from datetime import date, timedelta
from typing import Optional, List
from pydantic import BaseModel, field_validator, Field
from database.models import MovieStatusEnum


class ORMBaseModel(BaseModel):
    class Config:
        from_attributes = True


class Genre(BaseModel):
    id: int
    name: str


class Actor(BaseModel):
    id: int
    name: str


class Country(BaseModel):
    id: int
    code: str
    name: str | None


class Language(BaseModel):
    id: int
    name: str


class Movie(BaseModel):
    name: str
    date: date
    score: float
    overview: Optional[str] = None
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Country
    genres: List[Genre]
    actors: List[Actor]
    languages: List[Language]


class MovieDetail(Movie, ORMBaseModel):
    id: int


class MovieUpdate(ORMBaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    def date_not_too_far(cls, v: Optional[date]):
        if v and v > date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than 1 year in the future")
        return v

    @field_validator("score")
    def score_in_range(cls, v: float):
        if v < 0 or v > 100:
            raise ValueError("Score must be between 0 and 100")
        return v

    @field_validator("budget")
    def budget_non_negative(cls, v: float):
        if v < 0:
            raise ValueError("Budget cannot be negative")
        return v

    @field_validator("revenue")
    def revenue_non_negative(cls, v: float):
        if v < 0:
            raise ValueError("Revenue cannot be negative")
        return v


class MovieCreate(ORMBaseModel):
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

    @field_validator("date")
    def date_not_too_far(cls, v: Optional[date]):
        if v > (date.today() + timedelta(days=365)):
            raise ValueError("Release date cannot be more than 1 year in the future")
        return v

    @field_validator("score")
    def score_in_range(cls, v: float):
        if v < 0 or v > 100:
            raise ValueError("Score must be between 0 and 100")
        return v

    @field_validator("budget")
    def budget_non_negative(cls, v: float):
        if v < 0:
            raise ValueError("Budget cannot be negative")
        return v

    @field_validator("revenue")
    def revenue_non_negative(cls, v: float):
        if v < 0:
            raise ValueError("Revenue cannot be negative")
        return v


class MovieList(ORMBaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str] = None


class MovieListPagination(BaseModel):
    movies: List[MovieList]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
