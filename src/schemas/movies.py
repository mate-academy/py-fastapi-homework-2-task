from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, timedelta

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str = Field(max_length=3)
    name: Optional[str]


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class BasicMovieModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    @classmethod
    def date_not_too_far(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than 1 year in the future")
        return value


class MovieDetailSchema(BasicMovieModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateSchema(BasicMovieModel):
    model_config = ConfigDict(from_attributes=True)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def date_not_too_far(cls, value: Optional[date]) -> Optional[date]:
        if value and value > date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than 1 year in the future")
        return value
