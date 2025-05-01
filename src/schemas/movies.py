import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    # status: MovieStatusEnum
    # budget: Decimal
    # revenue: float
    # country_id: int
    # genres_ids: List[int] = []
    # actors_ids: List[int] = []
    # languages_ids: List[int] = []

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema] = []
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    class Config:
        from_attributes = True
