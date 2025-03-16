from typing import List
from pydantic import BaseModel

from routes import movies

# Write your code here


class MovieBase(BaseModel):
    id: int
    name: str
    date: str
    score: float
    overview: str
    status: str  # (Released | Post Production | In Production)
    budget: float  # (>= 0)
    revenue: float  # (>= 0)
    country: str  # (ISO 3166-1 alpha-3 code)",
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: str
    score: float
    overwiew: str


class MovieListResponseSchema(MovieBase):
    movies: List[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    class Config:
        from_attributes = True


class MovieCreate(MovieBase):
    pass


class MovieDetailSchema(MovieBase):
    pass


class MovieUpdate(MovieBase):
    pass
