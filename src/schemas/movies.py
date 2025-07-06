from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from datetime import date, timedelta
from typing import List, Optional


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    model_config = {
        "from_attributes": True
    }


class GenreSchema(BaseModel):
    id: int
    name: Optional[str] = None
    model_config = {
        "from_attributes": True
    }


class ActorSchema(BaseModel):
    id: int
    name: str
    model_config = {
        "from_attributes": True
    }


class LanguageSchema(BaseModel):
    id: int
    name: str
    model_config = {
        "from_attributes": True
    }


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]
    model_config = {
        "from_attributes": True
    }


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]
    model_config = {
        "from_attributes": True
    }

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Optional[date]):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYY-MM-DD.")
        if value and value > date.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return value


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    model_config = {
        "from_attributes": True
    }

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Optional[date]):
        if value and value > date.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return value


class MovieRead(MovieBase):
    id: int
    model_config = {
        "from_attributes": True
    }


class MovieShortSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    model_config = {
        "from_attributes": True
    }


class PaginatedMoviesResponse(BaseModel):
    movies: List[MovieShortSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
    model_config = {
        "from_attributes": True
    }


class MoviesListResponse(BaseModel):
    movies: List[MovieShortSchema]
