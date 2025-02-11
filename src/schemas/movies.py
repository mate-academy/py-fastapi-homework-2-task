from datetime import date as date_module, timedelta
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None


class GenresSchema(BaseModel):
    id: int
    name: str


class ActorsSchema(BaseModel):
    id: int
    name: str


class LanguagesSchema(BaseModel):
    id: int
    name: str


class MovieStatus(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"


class MovieListSchema(BaseModel):
    id: int
    name: str
    date: date_module
    score: float
    overview: str


class MoviePageSchema(BaseModel):
    movies: List[MovieListSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date_module
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountrySchema
    genres: List[GenresSchema]
    actors: List[ActorsSchema]
    languages: List[LanguagesSchema]


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date_module = Field(..., le=(date_module.today() + timedelta(days=365)))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date_module] = Field(None, le=(date_module.today() + timedelta(days=365)))
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None