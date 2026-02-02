from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from enum import Enum


class MovieStatusEnum(str, Enum):
    released = "Released"
    post_production = "Post Production"
    planned = "Planned"


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: Optional[date] = None
    score: float = 0.0
    overview: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class MoviePaginationSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieListItemSchema):
    status: Optional[MovieStatusEnum] = None
    budget: float = 0.0
    revenue: float = 0.0
    country: Optional[CountrySchema] = None
    genres: List[GenreSchema] = []
    actors: List[ActorSchema] = []
    languages: List[LanguageSchema] = []
    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str
    date: Optional[date] = None
    score: float = 0.0
    overview: Optional[str] = None
    status: MovieStatusEnum = MovieStatusEnum.released
    budget: float = 0.0
    revenue: float = 0.0
    country: Optional[str] = None
    genres: List[str] = []
    actors: List[str] = []
    languages: List[str] = []


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None