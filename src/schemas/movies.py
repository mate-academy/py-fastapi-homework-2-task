import datetime
from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str | None


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
    date: date
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
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def date_not_too_far(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return value


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
