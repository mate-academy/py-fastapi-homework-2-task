from pydantic import BaseModel
from typing import List, Optional

class Movie(BaseModel):
    id: int
    name: str
    date: str
    score: float
    overview: str

    class Config:
        orm_mode = True

class MoviesListResponse(BaseModel):
    movies: List[Movie]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
