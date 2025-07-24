from decimal import Decimal

from pydantic import (
    BaseModel,
    constr,
    confloat,
    field_validator,
    Field,
    ConfigDict
)
from datetime import date, timedelta
from typing import List, Optional

from src.database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: constr(max_length=255)
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: confloat(ge=0)
    revenue: confloat(ge=0)
    country: constr(min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far_future(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError("Invalid input data.")
        return value

    @field_validator("country")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        value = value.upper()
        if not value.isalpha():
            raise ValueError("Invalid country code")
        return value


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class GenreResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: Optional[constr(max_length=255)] = None
    date: Optional[date] = None
    score: Optional[confloat(ge=0, le=100)] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    revenue: Optional[confloat(ge=0)] = None
    country: Optional[constr(min_length=2, max_length=3)] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("date")
    @classmethod
    def validate_date_not_too_future_update(cls, value: date) -> date:
        if value is not None and value > date.today() + timedelta(days=365):
            raise ValueError('Date cannot be more than one year in the future.')
        return value
