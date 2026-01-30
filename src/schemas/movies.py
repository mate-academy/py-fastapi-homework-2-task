from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class CountryReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str | None = None


class GenreReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str | None = None


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


MovieStatus = Literal["Released", "Post Production", "In Production"]


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str | None = None
    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    country: str = Field(min_length=3, max_length=3)  # ISO alpha-3 code
    genres: list[str] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class MovieReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str | None = None
    status: MovieStatus
    budget: float
    revenue: float

    country: CountryReadSchema
    genres: list[GenreReadSchema]
    actors: list[ActorReadSchema]
    languages: list[LanguageReadSchema]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    date: date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatus | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
