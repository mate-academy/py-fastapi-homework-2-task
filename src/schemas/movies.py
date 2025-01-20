from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class GenreBase(BaseModel):
    name: str

    class Config:
        from_attributes = True


class ActorBase(BaseModel):
    name: str

    class Config:
        from_attributes = True


class CountryBase(BaseModel):
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class LanguageBase(BaseModel):
    name: str

    class Config:
        from_attributes = True


class MovieBase(BaseModel):
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieResponse(BaseModel):
    movies: List[MovieBase]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailResponseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    release_date: Optional[datetime] = None
    director: Optional[str] = None
    genre: Optional[str] = None
    duration_minutes: Optional[int] = None
    rating: Optional[float] = None
    language: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class GenreCreate(BaseModel):
    name: str


class ActorCreate(BaseModel):
    name: str


class LanguageCreate(BaseModel):
    name: str


class MovieCreateRequest(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True


class MovieCreateOptional(MovieCreateRequest):
    name: str = None
    date: date = None
    score: float = None
    overview: str = None
    status: MovieStatusEnum = None
    budget: float = None
    revenue: float = None
    country: str = None
    genres: List[str] = None
    actors: List[str] = None
    languages: List[str] = None


class MovieCreateResponse(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Optional[CountryBase] = None
    genres: List[GenreBase]
    actors: List[ActorBase]
    languages: List[LanguageBase]

    class Config:
        from_attributes = True
