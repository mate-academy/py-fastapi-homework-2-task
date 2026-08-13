from __future__ import annotations
import datetime
from pydantic import BaseModel
from pydantic import Field
from database.models import MovieStatusEnum


class NamedEntity(BaseModel):
    id: int
    name: str


class Genre(NamedEntity):
    pass


class Actor(NamedEntity):
    pass


class Language(NamedEntity):
    pass


class Country(BaseModel):
    id: int
    code: str
    name: str | None


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str


class MovieListItemSchema(MovieBase):
    id: int

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreate(MovieBase):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetailSchema(MovieBase):
    id: int
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Country
    genres: list[Genre]
    actors: list[Actor]
    languages: list[Language]

    class Config:
        from_attributes = True


class MovieUpdate(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
