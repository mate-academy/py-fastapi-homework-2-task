from datetime import date as Date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class NamedEntitySchema(ORMModel):
    id: int
    name: str


class CountrySchema(ORMModel):
    id: int
    code: str
    name: str | None


class MovieListItemSchema(ORMModel):
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


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[NamedEntitySchema]
    actors: list[NamedEntitySchema]
    languages: list[NamedEntitySchema]


class MovieDateValidation(BaseModel):
    @field_validator("date", check_fields=False)
    @classmethod
    def validate_release_date(cls, value: Date | None) -> Date | None:
        if value is None:
            return value
        today = Date.today()
        try:
            latest_date = today.replace(year=today.year + 1)
        except ValueError:  # February 29 in a leap year.
            latest_date = today.replace(year=today.year + 1, day=28)
        if value > latest_date:
            raise ValueError("Release date cannot be more than one year in the future")
        return value


class MovieCreateSchema(MovieDateValidation):
    name: str = Field(max_length=255)
    date: Date
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0, le=9_999_999_999_999.99, allow_inf_nan=False)
    revenue: float = Field(ge=0, allow_inf_nan=False)
    country: str = Field(pattern=r"^[A-Za-z]{2,3}$")
    genres: list[Annotated[str, Field(max_length=255)]]
    actors: list[Annotated[str, Field(max_length=255)]]
    languages: list[Annotated[str, Field(max_length=255)]]


class MovieUpdateSchema(MovieDateValidation):
    name: str | None = Field(default=None, max_length=255)
    date: Date | None = None
    score: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0, le=9_999_999_999_999.99, allow_inf_nan=False)
    revenue: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("*", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value
