# Write your code here
import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class Genre(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Actor(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Language(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Country(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country_id: int
    country: Country
    genres: list[Genre]
    actors: list[Actor]
    languages: list[Language]

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateResponseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date = Field(...)
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("date")
    def date_not_too_far_in_future(cls, value):
        one_year_from_now = datetime.date.today() + datetime.timedelta(days=365)
        if value > one_year_from_now:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieUpdateResponseSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    model_config = ConfigDict(from_attributes=True)
