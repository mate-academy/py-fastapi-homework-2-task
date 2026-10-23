from __future__ import annotations

from datetime import date as Date
from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from database.models import MovieStatusEnum


class ORMModelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(ORMModelSchema):
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


class CountrySchema(ORMModelSchema):
    id: int
    code: str
    name: str | None


class NamedEntitySchema(ORMModelSchema):
    id: int
    name: str


class GenreSchema(NamedEntitySchema):
    pass


class ActorSchema(NamedEntitySchema):
    pass


class LanguageSchema(NamedEntitySchema):
    pass


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieDataSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    date: Date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: Date) -> Date:
        if value > Date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than one year in the future.")
        return value


class MovieCreateSchema(MovieDataSchema):
    country: str = Field(min_length=2, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("country")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("genres", "actors", "languages")
    @classmethod
    def validate_related_names(cls, values: list[str]) -> list[str]:
        if any(not value or len(value) > 255 for value in values):
            raise ValueError("Related entity names must contain 1 to 255 characters.")

        # Repeated names would otherwise violate the association-table primary key.
        return list(dict.fromkeys(values))


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    date: Date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: Date | None) -> Date | None:
        if value is not None and value > Date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than one year in the future.")
        return value

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "MovieUpdateSchema":
        if any(
            getattr(self, field_name) is None
            for field_name in self.model_fields_set
        ):
            raise ValueError("Movie fields cannot be null.")
        return self


class MessageSchema(BaseModel):
    detail: str
