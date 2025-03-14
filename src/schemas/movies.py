from pydantic import BaseModel, constr
from typing import List, Optional
from datetime import date


class MovieCreate(BaseModel):
    name: constr(max_length=255)
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country_id: int
    genre_ids: List[int]
    actor_ids: List[int]
    language_ids: List[int]

    class Config:
        orm_mode = True


class MovieBase(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country_name: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        orm_mode = True


class MoviesList(BaseModel):
    movies: List[MovieBase]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class ErrorResponse(BaseModel):
    detail: str


class MovieResponse(MovieBase):
    country_name: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        orm_mode = True


class MovieUpdate(BaseModel):
    name: Optional[str]
    date: Optional[date]
    score: Optional[float]
    overview: Optional[str]
    status: Optional[str]
    budget: Optional[float]
    revenue: Optional[float]
    country_id: Optional[int]
    genre_ids: Optional[List[int]]
    actor_ids: Optional[List[int]]
    language_ids: Optional[List[int]]

    class Config:
        orm_mode = True
