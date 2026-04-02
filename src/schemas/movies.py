from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


MAX_FUTURE_DATE_DELTA = timedelta(days=365)


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        use_enum_values=True,
    )


class RelatedEntitySchema(BaseSchema):
    id: int
    name: str


class CountrySchema(BaseSchema):
    id: int
    code: str
    name: str | None


class MovieListItemSchema(BaseSchema):
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseSchema):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseSchema):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[RelatedEntitySchema]
    actors: list[RelatedEntitySchema]
    languages: list[RelatedEntitySchema]


class MovieCreateSchema(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str = Field(min_length=1)
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(min_length=2, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: date) -> date:
        if value > date.today() + MAX_FUTURE_DATE_DELTA:
            raise ValueError("Date must not be more than one year in the future.")
        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("genres", "actors", "languages")
    @classmethod
    def validate_string_list(cls, values: list[str]) -> list[str]:
        cleaned_values: list[str] = []
        for value in values:
            cleaned_value = value.strip()
            if not cleaned_value:
                raise ValueError("List items must not be empty.")
            if cleaned_value not in cleaned_values:
                cleaned_values.append(cleaned_value)
        return cleaned_values


class MovieUpdateSchema(BaseSchema):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = Field(default=None, min_length=1)
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today() + MAX_FUTURE_DATE_DELTA:
            raise ValueError("Date must not be more than one year in the future.")
        return value


class MessageSchema(BaseSchema):
    detail: str
