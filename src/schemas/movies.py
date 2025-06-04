from typing import Optional
from enum import Enum
from pydantic import BaseModel
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


class MovieCreateSchema(MovieDetailSchema):
    pass