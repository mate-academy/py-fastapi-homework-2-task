from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date as date_dt
from typing import Optional, List, Any
from enum import Enum


class MovieStatus(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


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


class MovieDetailSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    date: date_dt
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date_dt
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date_dt
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=2, max_length=3)  # ISO 3166-1 alpha-3 code
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator('date')
    def validate_date(cls, v):
        if v > date_dt.today().replace(year=date_dt.today().year + 1):
            raise ValueError('Date cannot be more than one year in the future')
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date_dt] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    model_config = ConfigDict(from_attributes=True)

    @field_validator('date')
    def validate_date(cls, v):
        if v and v > date_dt.today().replace(year=date_dt.today().year + 1):
            raise ValueError('Date cannot be more than one year in the future')
        return v
