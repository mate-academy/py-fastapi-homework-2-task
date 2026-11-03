import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MovieStatus(StrEnum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page : str | None = None
    total_pages: int
    total_items: int


class GenreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CountryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str | None = None


class MovieCreate(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetailSchema(MovieListItemSchema):
    model_config = ConfigDict(from_attributes=True)

    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryRead
    genres: list[GenreRead]
    actors: list[ActorRead]
    languages: list[LanguageRead]


class MovieUpdate(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatus | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
