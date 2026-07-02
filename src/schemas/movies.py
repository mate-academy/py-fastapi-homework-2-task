import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, field_validator

from database.models import MovieStatusEnum


class Genre(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Actor(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Country(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Language(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieValidationDateMixin(BaseModel):
    date: datetime.date

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(
        cls, v: datetime.date | None
    ) -> datetime.date | None:
        if v is None:
            return v
        max_allowed = datetime.date.today() + datetime.timedelta(days=365)
        if v > max_allowed:
            raise ValueError("date must not be more than one year in the future")
        return v


class MovieCreate(MovieValidationDateMixin):
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: Decimal = Field(ge=0, max_digits=15, decimal_places=2)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdate(MovieValidationDateMixin):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: Decimal | None = Field(default=None, ge=0, max_digits=15, decimal_places=2)
    revenue: float | None = Field(default=None, ge=0)


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Country
    genres: list[Genre]
    actors: list[Actor]
    languages: list[Language]
