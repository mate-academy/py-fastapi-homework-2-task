from datetime import date, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum

from database.models import MovieStatusEnum


class MovieStatus(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)


class MovieCreateSchema(MovieBase):
    country: str = Field(..., min_length=3, max_length=3)
    genres: List[str] = Field(..., min_length=1)
    actors: List[str] = Field(..., min_length=1)
    languages: List[str] = Field(..., min_length=1)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        max_date = date.today() + timedelta(days=365 * 2)
        if value > max_date:
            raise ValueError("Release date cannot be more than 2 years in the future")
        return value


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    country: Optional[str] = None
    genres: Optional[List[str]] = Field(None, min_length=1)
    actors: Optional[List[str]] = Field(None, min_length=1)
    languages: Optional[List[str]] = Field(None, min_length=1)


class CountryResponse(BaseModel):
    id: int
    code: str
    name: Optional[str]


class GenreResponse(BaseModel):
    id: int
    name: str


class ActorResponse(BaseModel):
    id: int
    name: str


class LanguageResponse(BaseModel):
    id: int
    name: str


class MovieShortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieFullResponse(MovieShortResponse):
    status: MovieStatus
    budget: float
    revenue: float
    country: CountryResponse
    genres: List[GenreResponse]
    actors: List[ActorResponse]
    languages: List[LanguageResponse]

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    movies: List[MovieShortResponse]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateResponse(BaseModel):
    detail: str
