from datetime import date, timedelta
from typing import List

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum
from schemas.actors import ActorRead
from schemas.countries import CountryRead
from schemas.genres import GenreRead
from schemas.languages import LanguageRead


class MovieBase(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float


class MovieValidationMixin(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)

    @classmethod
    @field_validator("date")
    def validate_date(cls, v: date):
        if v > date.today() + timedelta(days=365):
            raise ValueError("Release date must not be more than one year in the future.")
        return v


class MovieCreate(MovieValidationMixin, MovieBase):
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    release_date: date | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
    country: str | None = None
    genres: List[str] | None = None
    actors: List[str] | None = None
    languages: List[str] | None = None

    @classmethod
    @field_validator("release_date")
    def validate_date(cls, v: date | None):
        if v and v > date.today() + timedelta(days=365):
            raise ValueError("Release date must not be more than one year in the future.")
        return v


class MovieRead(MovieBase):
    id: int
    country: CountryRead
    genres: List[GenreRead]
    actors: List[ActorRead]
    languages: List[LanguageRead]

    class Config:
        from_attributes = True


class MovieListItem(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieList(BaseModel):
    movies: List[MovieListItem]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    class Config:
        from_attributes = True
