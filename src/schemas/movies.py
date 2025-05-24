from typing import Annotated, Optional

from datetime import date, timedelta

from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)
import pycountry

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


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
    def validate_date_not_exceed_one_year_future(cls, value):
        max_date = date.today() + timedelta(days=365)

        if value > max_date:
            raise ValueError("Date cannot exceed one year from today.")
        return value

    @field_validator("country")
    def validate_country_iso_alpha2_code(cls, value):
        alpha2_codes = [country.alpha_2 for country in pycountry.countries]

        if value not in alpha2_codes:
            raise ValueError(
                "Country code must be 'ISO 3166-1 alpha-2' format"
            )
        return value

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
    country: CountrySchema
    languages: list[LanguageSchema]
    genres: list[GenreSchema]
    actors: list[ActorSchema]

    model_config = ConfigDict(from_attributes=True)


class MoviePartialUpdateSchema(BaseModel):
    name: Annotated[Optional[str], Field(max_length=255, default=None)]
    date: Annotated[Optional[date], Field(default=None)]
    score: Annotated[Optional[float], Field(ge=0, le=100, default=None)]
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Annotated[Optional[float], Field(ge=0, default=None)]
    revenue: Annotated[Optional[float], Field(ge=0, default=None)]


class MoviePartialUpdateSuccessSchema(BaseModel):
    detail: str


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)
