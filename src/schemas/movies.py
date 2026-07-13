from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
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


class MovieDetailResponseSchema(BaseModel):
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
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)


class MessageSchema(BaseModel):
    detail: str
