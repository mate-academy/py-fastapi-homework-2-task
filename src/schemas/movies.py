from __future__ import annotations

from datetime import date as Date
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: Date
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


class NamedEntitySchema(BaseModel):
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
    genres: list[NamedEntitySchema]
    actors: list[NamedEntitySchema]
    languages: list[NamedEntitySchema]


def _one_year_from_today() -> Date:
    today = Date.today()
    try:
        return today.replace(year=today.year + 1)
    except ValueError:
        # February 29 has no counterpart in the following year.
        return today.replace(year=today.year + 1, day=28)


def _validate_release_date(value: Date) -> Date:
    if value > _one_year_from_today():
        raise ValueError("Date must not be more than one year in the future")
    return value


def _validate_finite_amount(value: float) -> float:
    if not isfinite(value):
        raise ValueError("Amount must be a finite number")
    return value


class MovieCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    date: Date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(min_length=2, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: Date) -> Date:
        return _validate_release_date(value)

    @field_validator("budget", "revenue")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        return _validate_finite_amount(value)

    @field_validator("country")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        code = value.strip().upper()
        if len(code) not in (2, 3) or not code.isalpha():
            raise ValueError("Country must be a two- or three-letter code")
        return code

    @field_validator("genres", "actors", "languages")
    @classmethod
    def clean_entity_names(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value or len(value) > 255 for value in cleaned):
            raise ValueError("Entity names must contain 1 to 255 characters")
        return cleaned


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    date: Date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "MovieUpdateSchema":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: Date | None) -> Date | None:
        return _validate_release_date(value) if value is not None else None

    @field_validator("budget", "revenue")
    @classmethod
    def validate_amount(cls, value: float | None) -> float | None:
        return _validate_finite_amount(value) if value is not None else None
