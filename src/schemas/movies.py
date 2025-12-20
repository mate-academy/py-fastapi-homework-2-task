import datetime
from typing import List

from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None


class GenreResponseSchema(BaseModel):
    id: int
    name: str


class ActorResponseSchema(BaseModel):
    id: int
    name: str


class LanguageResponseSchema(BaseModel):
    id: int
    name: str


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]


class MovieDetailSchema(BaseModel):
    pass

