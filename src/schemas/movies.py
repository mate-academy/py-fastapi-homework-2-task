from datetime import (
    date as dt_date,
    timedelta,
)
from typing import List, Optional
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
)
from enum import Enum


class MovieStatus(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"


class Country(BaseModel):
    id: int = Field(..., alias="id_", serialization_alias="id")
    code: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Genre(BaseModel):
    id: int = Field(..., alias="id_", serialization_alias="id")
    name: str

    model_config = ConfigDict(from_attributes=True)


class Actor(BaseModel):
    id: int = Field(..., alias="id_", serialization_alias="id")
    name: str

    model_config = ConfigDict(from_attributes=True)


class Language(BaseModel):
    id: int = Field(..., alias="id_", serialization_alias="id")
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    release_date: dt_date = Field(..., alias="date", serialization_alias="date")
    status: MovieStatus

    # Optional fields (nullable=True in ORM)
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    # ORM-Mode for inheritance
    model_config = ConfigDict(from_attributes=True)


class MovieShort(BaseModel):
    id: int = Field(..., alias="id_", serialization_alias="id")
    name: str
    release_date: dt_date = Field(..., alias="date", serialization_alias="date")
    score: Optional[float] = None
    overview: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovieFull(MovieBase):
    id: int = Field(..., alias="id_", serialization_alias="id")

    country: Optional[Country] = None

    genres: List[Genre] = Field(default_factory=list)
    actors: List[Actor] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255)
    release_date: dt_date

    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: MovieStatus
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("release_date")
    @classmethod
    def validate_release_date(cls, value: dt_date) -> dt_date:
        if value > dt_date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than 1 year in the future.")
        return value


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    release_date: Optional[dt_date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not (0 <= value <= 100):
            raise ValueError("Score must be between 0 and 100.")
        return value

    @field_validator("budget", "revenue")
    @classmethod
    def validate_non_negative(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("Budget and revenue must be non-negative.")
        return value


class MoviesListResponse(BaseModel):
    movies: List[MovieShort]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


MovieListResponseSchema = MoviesListResponse
MovieDetailSchema = MovieFull
MovieListItemSchema = MovieShort
