from datetime import timedelta, date as Date
from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


class NamedEntitySchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: Date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[NamedEntitySchema]
    actors: list[NamedEntitySchema]
    languages: list[NamedEntitySchema]

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: Date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreate(BaseModel):
    name: str
    date: Date
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
    name: str | None = None
    date: Date | None = None
    score: float | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None
    country: str | None = None
    genres: list[str] | None = None
    actors: list[str] | None = None
    languages: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)
