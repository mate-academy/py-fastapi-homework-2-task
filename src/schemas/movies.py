from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None

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


class MovieListResponseSchema(BaseModel):
    movies: list["MovieListItemSchema"]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieAddSchema(BaseModel):
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
    def date_lte_one_year_from_now(cls, v):
        if v <= date.today() + timedelta(days=365):
            return v
        raise ValueError("date must not be greater that one year in the future.")

    @field_validator("country")
    @classmethod
    def country_iso_code(cls, v):
        if len(v) == 2 and v.isalpha() and v.isupper():
            return v
        raise ValueError("country must be in ISO 3166-1 alpha-2 code format.")

    @field_validator("genres", "languages", "actors")
    @classmethod
    def capitalize_fields(cls, v):
        return [element.title() for element in v]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(max_length=255, default=None)
    date: Optional[date] = None
    score: Optional[float] = Field(ge=0, le=100, default=None)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(ge=0, default=None)
    revenue: Optional[float] = Field(ge=0, default=None)

    @field_validator("date")
    @classmethod
    def date_lte_one_year_from_now(cls, v):
        if v <= date.today() + timedelta(days=365):
            return v
        raise ValueError("date must not be greater that one year in the future.")
