from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MovieBaseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: Optional[float]
    genre: Optional[str]
    overview: Optional[str]
    crew: Optional[str]
    orig_title: Optional[str]
    status: Optional[str]
    orig_lang: Optional[str]
    budget: Optional[int]
    revenue: Optional[float]
    country: Optional[str]


class MovieCreateSchema(MovieBaseSchema):
    pass


class MovieUpdateSchema(MovieBaseSchema):
    pass


class MovieReadSchema(MovieBaseSchema):
    id: int

    class Config:
        from_attributes = True


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: Optional[float]
    genre: Optional[str]
    overview: Optional[str]
    crew: Optional[str]
    orig_title: Optional[str]
    status: Optional[str]
    orig_lang: Optional[str]
    budget: Optional[int]
    revenue: Optional[float]
    country: Optional[str]

    class Config:
        from_attributes: True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieDetailResponseSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
