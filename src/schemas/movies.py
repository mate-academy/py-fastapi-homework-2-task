import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class MovieBase(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieRead(MovieBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    movies: List[MovieRead]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)
