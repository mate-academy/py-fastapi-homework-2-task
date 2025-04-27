import datetime
import re

from pydantic import BaseModel, Field, field_validator

from typing import List, Optional

from database.models import MovieStatusEnum
from schemas import (
    CountryDetailSchema,
    GenreDetailSchema,
    ActorDetailSchema,
)
from schemas.languages import LanguageDetailSchema


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryDetailSchema
    genres: List[GenreDetailSchema]
    actors: List[ActorDetailSchema]
    languages: List[LanguageDetailSchema]

    class Config:
        from_attributes = True


class MovieListSchema(BaseModel):
    id: int
    name: str
    overview: str
    date: datetime.date
    score: float


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    def validate_date(cls, value: datetime.date) -> datetime.date:
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        if len(value) != 3 or not re.match(r'^[A-Z]{3}$', value):
            raise ValueError("Country code must be a 3-letter uppercase string.")
        return value
