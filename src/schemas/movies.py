from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: Optional[str] = None


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


class MovieListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: str


class PaginatedMoviesResponse(BaseModel):
    movies: List[MovieListOut]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., description="ISO 3166-1 alpha-3 code")
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        max_date = date.today() + timedelta(days=365)
        if v > max_date:
            raise ValueError("The date must not be more than one year in the future.")
        return v


class MovieDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Optional[CountrySchema] = None
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
