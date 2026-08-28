from datetime import date as Date
from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    date: Date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[NamedEntitySchema]
    actors: list[NamedEntitySchema]
    languages: list[NamedEntitySchema]


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: Date
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
    def validate_release_date(cls, value: Date) -> Date:
        if value > Date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than one year in the future.")
        return value

    @field_validator("country")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) not in (2, 3):
            raise ValueError("Country code must contain two or three characters.")
        return value

    @field_validator("genres", "actors", "languages")
    @classmethod
    def normalize_names(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            value = value.strip()
            if not value:
                raise ValueError("Related entity names cannot be empty.")
            if len(value) > 255:
                raise ValueError("Related entity names cannot exceed 255 characters.")
            if value not in normalized:
                normalized.append(value)
        return normalized


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    date: Date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = Field(default=None, min_length=1)
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: Date | None) -> Date | None:
        if value is not None and value > Date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than one year in the future.")
        return value
