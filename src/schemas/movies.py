from datetime import date, datetime, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.database.models import MovieStatusEnum


class NamedEntitySchema(BaseModel):
    id: int
    name: str = Field(max_length=255)


class CountryResponseSchema(BaseModel):
    id: int
    name: str | None = Field(max_length=255)
    code: str = Field(max_length=3)


class GenreResponseSchema(NamedEntitySchema):
    pass


class ActorResponseSchema(NamedEntitySchema):
    pass


class LanguageResponseSchema(NamedEntitySchema):
    pass


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date | datetime
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date | datetime) -> date | datetime:
        check_date = v.date() if isinstance(v, datetime) else v

        if check_date > date.today() + timedelta(days=365):
            raise ValueError(
                "The date must not be more than one year in the future.")
        return v


class MovieDetailResponseSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]


class MovieCreateRequestSchema(MovieBaseSchema):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date | datetime
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateRequestSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: date | datetime | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)


class MessageResponseSchema(BaseModel):
    detail: str
