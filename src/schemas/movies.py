import datetime
from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ValidationError

from database.models import MovieStatusEnum


class RelatedEntitySchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {
        "from_attributes": True
    }


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {
        "from_attributes": True
    }


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    overview: str
    score: float = Field(ge=0, le=100)
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3, min_length=2)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        max_date = date.today() + timedelta(days=365)
        if value > max_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    overview: str
    score: float
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[RelatedEntitySchema]
    actors: list[RelatedEntitySchema]
    languages: list[RelatedEntitySchema]

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
