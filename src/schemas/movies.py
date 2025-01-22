from pydantic import BaseModel, Field
import datetime
from typing import Optional
from enum import Enum


class MovieStatus(str, Enum):
    RELEASED: str = "Released"
    POST_PRODUCTION: str = "Post Production"
    IN_PRODUCTION: str = "In Production"


class Movie(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatus
    budget: float
    revenue: float


class Genre(BaseModel):
    name: str
    movies: list[Movie]

    model_config = {"from_attributes": True}


class GenreDetail(BaseModel):
    id: int
    name: str


class Actor(BaseModel):
    name: str
    movies: list[Movie]

    model_config = {"from_attributes": True}


class ActorDetail(BaseModel):
    id: int
    name: str


class Language(BaseModel):
    name: str
    movies: list[Movie]

    model_config = {"from_attributes": True}


class LanguageDetail(BaseModel):
    id: int
    name: str


class Country(BaseModel):
    code: str
    name: Optional[str]
    movies: list[Movie]

    model_config = {"from_attributes": True}


class CountryDetail(BaseModel):
    id: int
    code: str
    name: Optional[str]


class MovieCreate(BaseModel):
    name: str = Field(max_length=255)
    date: (
        datetime.date
    )
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = {"from_attributes": True}


class MovieDetail(Movie):
    id: int
    country: Optional[CountryDetail] = None
    genres: Optional[list[GenreDetail]] = None
    actors: Optional[list[ActorDetail]] = None
    languages: Optional[list[LanguageDetail]] = None


class MovieList(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponse(BaseModel):
    movies: list[MovieList]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieUpdate(Movie):
    name: Optional[str] = Field(max_length=255, default=None)
    date: Optional[datetime.date] = Field(
        lt=datetime.date.today() + datetime.timedelta(days=365), default=None
    )
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    score: Optional[float] = Field(ge=0, le=100, default=None)
    budget: Optional[float] = Field(gt=0, default=None)
    revenue: Optional[float] = Field(gt=0, default=None)
