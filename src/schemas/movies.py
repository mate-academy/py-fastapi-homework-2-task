from pydantic import (BaseModel,
                      ConfigDict,
                      Field,
                      field_validator)
from datetime import date, timedelta
from typing import List, Optional

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str] = None


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None


class MovieBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieDetailResponseSchema(MovieBase):
    pass


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator('date')
    @classmethod
    def validate_future_date(cls, v: date):
        if v > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return v


class MovieSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator('date')
    @classmethod
    def validate_future_date(cls, v: Optional[date]):
        if v is not None and v > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return v


class MovieListResponseSchema(BaseModel):
    movies: List[MovieSummarySchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
