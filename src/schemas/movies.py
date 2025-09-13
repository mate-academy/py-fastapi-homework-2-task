from datetime import timedelta, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from src.database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

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


# --- movie schemas ---

class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    def validate_date(cls, value):
        max_date = date.today() + timedelta(days=365)
        if value > max_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(MovieBase):
    pass


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    country: Optional[str] = Field(None, min_length=2, max_length=3)
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    @field_validator("date")
    def validate_date(cls, value):
        if value is None:
            return value
        max_date = date.today() + timedelta(days=365)
        if value > max_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str

    @field_validator("date")
    def validate_date(cls, value):
        max_date = date.today() + timedelta(days=365)
        if value > max_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieOut(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    @field_validator("date")
    def validate_date(cls, value):
        max_date = date.today() + timedelta(days=365)
        if value > max_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieOut):
    pass
