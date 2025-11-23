import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.database.models import MovieStatusEnum
from src.schemas.actors import ActorRead
from src.schemas.countries import CountryRead
from src.schemas.genres import GenreRead
from src.schemas.languages import LanguageRead


class MovieBase(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country_id: int

    class Config:
        from_attributes = True


class MovieCreate(MovieBase):
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdate(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None
    country_id: int | None = None
    genres: List[str] | None = None
    actors: List[str] | None = None
    languages: List[str] | None = None


class MovieListItem(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponse(BaseModel):
    movies: List[MovieListItem]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetail(MovieBase):
    id: int
    country: CountryRead
    genres: List[GenreRead]
    actors: List[ActorRead]
    languages: List[LanguageRead]

    class Config:
        from_attributes = True
