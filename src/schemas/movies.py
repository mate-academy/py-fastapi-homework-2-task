from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from datetime import date

from src.database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str


class MovieCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float

    country: str
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: Optional[str]
    date: Optional[date]
    score: Optional[float]
    overview: Optional[str]
    status: Optional[MovieStatusEnum]
    budget: Optional[float]
    revenue: Optional[float]


class MovieListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id = int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListSchema]
    prev_page: Optional[int]
    next_page: Optional[int]
    total_pages: int
    total_items: int
