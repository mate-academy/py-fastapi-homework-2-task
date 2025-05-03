import datetime
from pydantic import BaseModel, Field, constr
from typing import List, Optional
from enum import Enum


class MovieShort(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MoviesList(BaseModel):
    movies: List[MovieShort]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieCreate(BaseModel):
    name: constr(min_length=1)
    date: datetime.date
    score: float = Field(..., ge=0.0, le=100.0)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0.0)
    revenue: float = Field(..., ge=0.0)
    country: constr(min_length=1)
    genres: List[constr(min_length=1)]
    actors: List[constr(min_length=1)]
    languages: List[constr(min_length=1)]

    class Config:
        arbitrary_types_allowed = True


class CountryOut(BaseModel):
    id: int
    code: str
    name: Optional[str]


class GenreOut(BaseModel):
    id: int
    name: str


class ActorOut(BaseModel):
    id: int
    name: str


class LanguageOut(BaseModel):
    id: int
    name: str


class MovieDetail(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryOut
    genres: List[GenreOut]
    actors: List[ActorOut]
    languages: List[LanguageOut]

    class Config:
        arbitrary_types_allowed = True


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    score: Optional[float] = None
    date: Optional[datetime.date] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[dict] = None
    genres: Optional[list] = None
    actors: Optional[list] = None
    languages: Optional[list] = None
