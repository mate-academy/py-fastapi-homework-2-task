from __future__ import annotations

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: Optional[float] = None
    overview: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    total_items: int
    total_pages: int
    prev_page: Optional[str] = None
    next_page: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[CountrySchema] = None
    genres: List[GenreSchema] = Field(default_factory=list)
    actors: List[ActorSchema] = Field(default_factory=list)
    languages: List[LanguageSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[str] = None
    country_id: Optional[int] = None
    genres: Optional[List[str]] = Field(default_factory=list)
    actors: Optional[List[str]] = Field(default_factory=list)
    languages: Optional[List[str]] = Field(default_factory=list)

    genre_ids: Optional[List[int]] = Field(default_factory=list)
    actor_ids: Optional[List[int]] = Field(default_factory=list)
    language_ids: Optional[List[int]] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Inception",
                "date": "2010-07-16",
                "score": 8.8,
                "genres": ["Action", "Adventure"],
                "actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
                "languages": ["English", "French"]
            }
        }
    )


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    release_date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    actor_ids: Optional[List[int]] = None
    language_ids: Optional[List[int]] = None

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateResponseSchema(BaseModel):
    detail: str
    movie: MovieDetailSchema

    model_config = ConfigDict(from_attributes=True)
