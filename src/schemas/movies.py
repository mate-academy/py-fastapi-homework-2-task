from datetime import date
from typing import Optional, Annotated

from database.models import MovieStatusEnum
from validation import validate_future_limit
from pydantic import BaseModel, ConfigDict, Field, AfterValidator


class LanguageBase(BaseModel):
    id: int
    name: str


class CountryBase(BaseModel):
    id: int
    name: str | None
    code: str


class ActorBase(BaseModel):
    id: int
    name: str


class GenreBase(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country_id: int


class MovieDetailSchema(MovieBase):
    id: int
    country: Optional[CountryBase] | None = None
    genres: list[GenreBase] = []
    actors: list[ActorBase] = []
    languages: list[LanguageBase] = []


ValidReleaseDate = Annotated[date, AfterValidator(validate_future_limit)]


class MovieCreate(MovieBase):
    name: str = Field(max_length=255)
    score: float = Field(le=100, ge=0)
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country_id: Optional[int] = None
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]
    date: ValidReleaseDate


class MovieUpdate(MovieBase):
    name: Optional[str] = None
    date: Optional[ValidReleaseDate] = None
    score: Optional[float] = Field(default=None, le=100, ge=0)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
    country_id: Optional[int] = None


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int
