import datetime
from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field, constr


class MovieStatus(StrEnum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class CountryRead(BaseModel):
    id: int
    code: str
    name: Optional[str]


class GenreRead(BaseModel):
    id: int
    name: str


class ActorRead(BaseModel):
    id: int
    name: str


class LanguageRead(BaseModel):
    id: int
    name: str


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255, min_length=2)
    date: datetime.date = Field(..., alias="date")
    score: float = Field(..., ge=0, le=100, alias="score")
    overview: str = Field(..., min_length=20, max_length=2000)
    status: MovieStatus
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: constr(pattern=r"^[A-Z]{3}$")
    genres: List[str] = Field(..., min_length=1, max_length=12)
    actors: List[str] = Field(..., min_length=1, max_length=20)
    languages: List[str] = Field(..., min_length=1, max_length=20)


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    class Config:
        extra = "forbid"
        validate_assignment = True


class MovieListItem(BaseModel):  # для списку
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True

class MovieListResponse(BaseModel):
    movies: list[MovieListItem]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int

    class Config:
        from_attributes = True


class MovieDetailRead(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatus
    budget: float
    revenue: float
    country: CountryRead
    genres: list[GenreRead]
    actors: list[ActorRead]
    languages: list[LanguageRead]
