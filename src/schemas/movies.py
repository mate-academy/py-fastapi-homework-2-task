import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum
from schemas.actors import ActorResponseSchema
from schemas.countries import CountryResponseSchema
from schemas.genres import GenreResponseSchema
from schemas.languages import LanguageResponseSchema


class MovieBaseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str


class MovieListItemSchema(MovieBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(MovieBaseSchema):
    id: int
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieAddedSchema(MovieBaseSchema):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
