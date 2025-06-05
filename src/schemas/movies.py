from typing import Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import date


class MovieListResponseSchema(BaseModel):
    id: int
    name: str
    date: date | str
    score: float
    overview: str

    class Config:
        orm_mode = True


class PaginatedMoviesResponseSchema(BaseModel):
    movies: list[MovieListResponseSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None

    class Config:
        orm_mode = True


class GenresResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class ActorResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class LanguageResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class MovieStatus(str, Enum):
    released = "Released"
    upcoming = "Post Production"
    canceled = "In Production"


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date | str
    score: float
    overview: str
    status: MovieStatus
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenresResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    class Config:
        orm_mode = True


class MovieCreateSchema(BaseModel):
    name: str
    date: Union[date, str]
    score: float
    overview: str
    status: MovieStatus
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        orm_mode = True


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatus
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        orm_mode = True


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    overview: Optional[str] = None
    status: Optional[str] = Field(None, max_length=15, pattern="^(Released|Post Production|In Production)$")
