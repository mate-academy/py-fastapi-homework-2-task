import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: Decimal
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema] = []
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}
