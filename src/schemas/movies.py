from pydantic import BaseModel, confloat, constr
from datetime import date
from typing import List, Optional
from enum import Enum

class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"

class MovieListItem(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

class MovieListResponse(BaseModel):
    movies: List[MovieListItem]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

class CountryResponse(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

class GenreResponse(BaseModel):
    id: int
    name: str

class ActorResponse(BaseModel):
    id: int
    name: str

class LanguageResponse(BaseModel):
    id: int
    name: str

class MovieDetailResponse(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponse
    genres: List[GenreResponse]
    actors: List[ActorResponse]
    languages: List[LanguageResponse]

class MovieCreateRequest(BaseModel):
    name: str
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: confloat(ge=0)
    revenue: confloat(ge=0)
    country: constr(min_length=3, max_length=3)
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
