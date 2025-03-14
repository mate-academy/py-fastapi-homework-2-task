from datetime import date
from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = {"from_attributes": True}


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country_id: int

    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str | None
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = {"from_attributes": True}
