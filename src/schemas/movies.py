from __future__ import annotations

import decimal
from datetime import date as date_type

from pydantic import BaseModel, ConfigDict, Field, field_validator

from validators.movies import validate_movie_date
from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date_type
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    _validate_date = field_validator("date")(validate_movie_date)

    model_config = ConfigDict(from_attributes=True)


class MovieListSchema(BaseModel):
    id: int
    name: str
    date: date_type
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int = Field(ge=0)
    total_items: int = Field(ge=0)


class MovieCreateRequestSchema(MovieBaseSchema):
    country: str = Field(min_length=2, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetailSchema(MovieBaseSchema):
    id: int
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieUpdateRequestSchema(BaseModel):
    name: str | None = None
    date: date_type | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: decimal.Decimal | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    _validate_date = field_validator("date")(validate_movie_date)