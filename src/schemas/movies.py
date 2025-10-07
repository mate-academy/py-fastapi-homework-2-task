from datetime import date, timedelta
from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: Optional[str]
    name: Optional[str]


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieStatus(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str
    status: Optional[MovieStatus]
    budget: Optional[float]
    revenue: Optional[float]
    country: Optional[CountrySchema]
    genres: Optional[list[GenreSchema]] = None
    actors: Optional[list[ActorSchema]] = None
    languages: Optional[list[LanguageSchema]] = None


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: Annotated[float, Field(ge=0)] = None
    revenue: Annotated[float, Field(ge=0)] = None
    country: Optional[str] = Field(None, description="ISO 3166-1 alpha-3 code")
    genres: Optional[list[str]] = None
    actors: Optional[list[str]] = None
    languages: Optional[list[str]] = None

    @field_validator("date")
    def validate_date(cls, value):
        max_allowed = date.today() + timedelta(days=365)
        if value > max_allowed:
            raise ValueError("Date cannot be more than one year in the future.")
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

    @field_validator("date")
    def validate_date(cls, value):
        if value is not None:
            max_allowed = date.today() + timedelta(days=365)
            if value > max_allowed:
                raise ValueError("Date cannot be more than one year in the future.")
        return value
