from __future__ import annotations

from datetime import date, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, confloat, validator


class MovieStatus(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float | None = None
    overview: str | None = None


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None


class NamedEntitySchema(BaseModel):
    id: int
    name: str


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float | None = None
    overview: str | None = None
    status: str | None = None
    budget: float | None = None
    revenue: float | None = None

    country: CountrySchema | None = None
    genres: list[NamedEntitySchema] = []
    actors: list[NamedEntitySchema] = []
    languages: list[NamedEntitySchema] = []


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date

    score: Optional[confloat(ge=0, le=100)] = None  # type: ignore[misc]

    overview: Optional[str] = None
    status: Optional[MovieStatus] = None

    budget: Optional[confloat(ge=0)] = None  # type: ignore[misc]
    revenue: Optional[confloat(ge=0)] = None  # type: ignore[misc]

    country: str = Field(..., min_length=2, max_length=3)

    genres: list[str] = []
    actors: list[str] = []
    languages: list[str] = []

    @validator("date")
    def validate_date_not_too_far(cls, v: date) -> date:
        if v > (date.today() + timedelta(days=365)):
            raise ValueError("Invalid input data.")
        return v



class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[confloat(ge=0, le=100)] = None  # type: ignore[misc]
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[confloat(ge=0)] = None  # type: ignore[misc]
    revenue: Optional[confloat(ge=0)] = None  # type: ignore[misc]

    @validator("date")
    def validate_date_not_too_far(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        if v > (date.today() + timedelta(days=365)):
            raise ValueError("Invalid input data.")
        return v


class MessageSchema(BaseModel):
    detail: str
