from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum
from schemas.iso3166 import ISO_3166_1_ALPHA_3


TIME_ZONE = ZoneInfo("Europe/Kyiv")


def validate_movie_date_not_too_far(value: Optional[date]) -> Optional[date]:
    if value is None:
        return value
    today = datetime.now(TIME_ZONE).date()
    max_date = today + timedelta(days=365)
    if value > max_date:
        raise ValueError("Date cannot be more than one year in the future.")
    return value


def validate_iso3166_alpha3_country_code(value: str) -> str:
    code = value.strip().upper()
    if code not in ISO_3166_1_ALPHA_3:
        raise ValueError("Country must be a valid ISO 3166-1 alpha-3 code.")
    return code


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str]


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
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=3, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far(cls, value: date) -> date:
        return validate_movie_date_not_too_far(value)

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return validate_iso3166_alpha3_country_code(value)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far(cls, value: Optional[date]) -> Optional[date]:
        return validate_movie_date_not_too_far(value)


class MessageResponseSchema(BaseModel):
    detail: str
