from pydantic import BaseModel, ConfigDict, field_validator
import datetime
from typing import Optional
from src.database.models import MovieStatusEnum


class ActorSchema(BaseModel):
    id: int
    name: Optional[str] = None
    model_config: ConfigDict = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: Optional[str] = None
    model_config: ConfigDict = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: Optional[str] = None
    model_config: ConfigDict = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: Optional[str] = None
    name: Optional[str] = None

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Optional[str] = ""
    genres: Optional[list[str]] = []
    actors: Optional[list[str]] = []
    languages: Optional[list[str]] = []

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[int] = None
    country: Optional[str] = None
    genres: Optional[list[str]] = None
    actors: Optional[list[str]] = None
    languages: Optional[list[str]] = None

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    actors: Optional[list[ActorSchema]] = []
    genres: Optional[list[GenreSchema]] = []
    languages: Optional[list[LanguageSchema]] = []
    country: Optional[CountrySchema] = None


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config: ConfigDict = ConfigDict(from_attributes=True)
