import datetime
from pydantic import BaseModel
from typing import List, Optional

from database.models import MovieStatusEnum


class GenreRead(BaseModel):
    id: int
    name: str


class ActorRead(BaseModel):
    id: int
    name: str


class CountryRead(BaseModel):
    id: int
    code: str
    name: Optional[str]


class LanguageRead(BaseModel):
    id: int
    name: str


class Movies(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None


class MovieCreate(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieRead(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryRead
    genres: List[GenreRead]
    actors: List[ActorRead]
    languages: List[LanguageRead]

    class Config:
        orm_mode = True


class PaginationPages(BaseModel):
    movies: List[Movies]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
