import datetime
from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


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


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str = Field(min_length=1)
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(min_length=2, max_length=3)
    genres: list[str] = Field(min_length=1)
    actors: list[str] = Field(min_length=1)
    languages: list[str] = Field(min_length=1)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: date) -> date:
        max_allowed_date = date.today() + timedelta(days=365)

        if value > max_allowed_date:
            raise ValueError(
                "Date cannot be more than one year in the future"
            )

        return value


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )
    overview: Optional[str] = Field(
        default=None,
        min_length=1,
    )
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(
        default=None,
        ge=0,
    )
    revenue: Optional[float] = Field(
        default=None,
        ge=0,
    )


class DetailMessageSchema(BaseModel):
    detail: str
