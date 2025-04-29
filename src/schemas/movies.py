from datetime import date
from typing import List, Optional

from pydantic import BaseModel, confloat
from database.models import MovieStatusEnum


class CountryResponse(BaseModel):
    id: int
    code: str
    name: str | None


class GenreResponse(BaseModel):
    id: int
    name: str


class ActorResponse(BaseModel):
    id: int
    name: str


class LanguageResponse(BaseModel):
    id: int
    name: str


class MovieShortInfo(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MoviesListResponse(BaseModel):
    movies: List[MovieShortInfo]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateRequest(BaseModel):
    name: str
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: confloat(ge=0)
    revenue: confloat(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateRequest(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[confloat(ge=0, le=100)] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[confloat(ge=0)] = None
    revenue: Optional[confloat(ge=0)] = None


class MovieDetailInfo(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponse
    genres: List[GenreResponse]
    actors: List[ActorResponse]
    languages: List[LanguageResponse]
