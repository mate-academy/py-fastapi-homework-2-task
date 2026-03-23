from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str]


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    date: date
    score: float
    overview: str


class MovieDetailSchema(MovieBaseSchema):
    id: int
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieListResponseSchema(MovieBaseSchema):
    id: int


class MovieListItemSchema(BaseModel):
    movies: list[MovieListResponseSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    overview: str
    status: MovieStatusEnum
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]
