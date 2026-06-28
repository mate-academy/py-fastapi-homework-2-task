import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


CountryCode = Annotated[str, Field(min_length=2, max_length=3)]


def validate_movie_date(value: datetime.date) -> datetime.date:
    max_date = datetime.date.today() + datetime.timedelta(days=365)
    if value > max_date:
        raise ValueError("Date cannot be more than one year in the future.")
    return value


class CountryReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: CountryCode
    name: str | None = None


class NestedItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(cls, value: datetime.date) -> datetime.date:
        return validate_movie_date(value)


class MovieCreateSchema(MovieBaseSchema):
    country: CountryCode
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(cls, value: datetime.date | None) -> datetime.date | None:
        if value is None:
            return value
        return validate_movie_date(value)


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryReadSchema
    genres: list[NestedItemSchema]
    actors: list[NestedItemSchema]
    languages: list[NestedItemSchema]


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
