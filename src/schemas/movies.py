from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


def _validate_release_date(value: date) -> date:
    if value > date.today() + timedelta(days=365):
        raise ValueError("The date must not be more than one year in the future.")
    return value


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str] = None


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


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0.0, le=100.0)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0.0)
    revenue: float = Field(ge=0.0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def date_validator(cls, value: date) -> date:
        return _validate_release_date(value)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0.0)
    revenue: Optional[float] = Field(default=None, ge=0.0)

    @field_validator("date")
    @classmethod
    def date_validator(cls, value: date) -> date:
        if value is None:
            return value
        return _validate_release_date(value)
