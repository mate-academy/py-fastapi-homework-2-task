from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List, Optional
from decimal import Decimal
from src.database.models import MovieStatusEnum


class GenreRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class ActorRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class CountryRead(BaseModel):
    id: int
    code: str
    name: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class LanguageRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    status: MovieStatusEnum

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    items: List[MovieListItemSchema]
    total: int


class MovieDetailSchema(MovieListItemSchema):
    overview: str
    budget: Decimal
    revenue: float
    country: CountryRead
    genres: List[GenreRead]
    actors: List[ActorRead]
    languages: List[LanguageRead]


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: Decimal
    revenue: float
    country_id: int
    genre_ids: List[int] = []
    actor_ids: List[int] = []
    language_ids: List[int] = []


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[Decimal] = None
    revenue: Optional[float] = None
    country_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    actor_ids: Optional[List[int]] = None
    language_ids: Optional[List[int]] = None
