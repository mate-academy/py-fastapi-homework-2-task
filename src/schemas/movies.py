import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum
from schemas import references


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(min_length=2, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(cls, v: datetime.date) -> datetime.date:
        one_year_ahead = datetime.date.today().replace(
            year=datetime.date.today().year + 1
        )
        if v > one_year_ahead:
            raise ValueError("Release date cannot be more than one year in the future.")
        return v

    @field_validator("country")
    @classmethod
    def country_must_be_alpha3(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("Country must be a valid ISO 3166-1 alpha-3 code (letters only).")
        return v.upper()


class MovieCreateResponseSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: references.Country
    genres: list[references.Genre]
    actors: list[references.Actor]
    languages: list[references.Language]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
