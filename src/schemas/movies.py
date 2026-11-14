import datetime
from typing import Any

import pycountry
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator
)

from database.models import MovieStatusEnum


class MovieModelBase(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    budget: float
    revenue: float
    status: MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id_: int = Field(alias="id")
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


class CountrySchema(BaseModel):
    id_: int = Field(alias="id")
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id_: int = Field(alias="id")
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(GenreSchema):
    pass


class LanguageSchema(GenreSchema):
    pass


class MovieSchema(MovieModelBase):
    id_: int = Field(alias="id")
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(MovieModelBase):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]
    name: str = Field(max_length=255)
    score: float = Field(ge=0, le=100)
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_unique_values(self):
        for field in ("genres", "actors", "languages"):
            values = getattr(self, field)

            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate values in {field}")

        return self

    @field_validator("date")
    @classmethod
    def validate_date(
            cls,
            value: datetime.date
    ) -> datetime.date:
        today = datetime.date.today()

        try:
            max_date = today.replace(year=today.year + 1)
        except ValueError:
            max_date = today.replace(
                year=today.year + 1,
                day=28
            )

        if value > max_date:
            raise ValueError(
                "Date cannot be more than one year in the future"
            )

        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        value = value.upper()

        if pycountry.countries.get(alpha_3=value) is None:
            raise ValueError("Invalid country code.")

        return value


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = Field(default=None)
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = Field(default=None)
    status: MovieStatusEnum | None = Field(default=None)
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if any(value is None for value in values.values()):
                raise ValueError("Null values are not allowed.")

        return values
