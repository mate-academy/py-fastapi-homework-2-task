from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class CountryResponse(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)


class MessageResponse(BaseModel):
    detail: str


class MovieCreate(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(
        min_length=2,
        max_length=3,
        description="ISO 3166-1 alpha-3 code"
    )
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, v: date) -> date:
        today = date.today()
        max_future_date = today + timedelta(days=365)
        if v > max_future_date:
            raise ValueError("The date must not be more than one year in the future.")
        return v


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponse
    genres: list[ItemResponse]
    actors: list[ItemResponse]
    languages: list[ItemResponse]

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
