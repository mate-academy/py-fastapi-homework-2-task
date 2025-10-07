from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, List

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)

from database.models import MovieStatusEnum


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: Optional[str] = None
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryBaseSchema
    genres: List[GenreBaseSchema]
    actors: List[ActorBaseSchema]
    languages: List[LanguageBaseSchema]


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieDetailSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class CountryBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str = Field(max_length=3)
    name: Optional[str] = None


class GenreBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LanguageBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MovieCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def _date_no_more_than_year_from_now(cls, day: date) -> date:
        if day > date.today() + timedelta(days=365):
            raise ValueError("The date is too far away")
        return day


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None


class MovieReadSchema(MovieDetailSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int
