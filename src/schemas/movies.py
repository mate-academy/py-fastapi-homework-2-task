from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional

from database.models import MovieStatusEnum
from pydantic_extra_types.country import CountryAlpha3, CountryAlpha2


class MovieBaseSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str = Field(min_length=1)
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryAlpha2 | CountryAlpha3
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        if v > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future")
        return v


class MovieCountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: CountryAlpha2 | CountryAlpha3
    name: str | None


class MovieGenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieLanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MessageResponseSchema(BaseModel):
    detail: str


class MovieCreateSchema(MovieBaseSchema):
    pass


class MovieDetailSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: MovieCountrySchema
    genres: list[MovieGenreSchema]
    actors: list[MovieActorSchema]
    languages: list[MovieLanguageSchema]


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: Optional[date] = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        if v > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future")
        return v
