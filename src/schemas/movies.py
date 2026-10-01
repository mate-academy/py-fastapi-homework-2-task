import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MovieStatusLiteral = Literal["Released", "Post Production", "In Production"]


class MovieBase(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListItemSchema(MovieBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(MovieBase):
    name: str = Field(max_length=255)
    score: float = Field(ge=0, le=100)
    status: MovieStatusLiteral
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def date_not_far_future(cls, value: datetime.date) -> datetime.date:
        limit = datetime.date.today() + datetime.timedelta(days=365)
        if value > limit:
            raise ValueError("date must not be more than one year in the future")
        return value


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class GenreActorLanguageResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreateResponseSchema(MovieBase):
    id: int
    status: str
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenreActorLanguageResponseSchema]
    actors: list[GenreActorLanguageResponseSchema]
    languages: list[GenreActorLanguageResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieCreateResponseSchema):
    pass


class MovieUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusLiteral | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def date_not_far_future(
        cls, value: datetime.date | None
    ) -> datetime.date | None:
        if value is None:
            return value
        limit = datetime.date.today() + datetime.timedelta(days=365)
        if value > limit:
            raise ValueError("date must not be more than one year in the future")
        return value
