import datetime
from typing import Generic, TypeVar, List, Optional

from pydantic import BaseModel, ConfigDict, AnyHttpUrl

M = TypeVar("M")


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel, Generic[M]):
    movies: List[M]
    prev_page: Optional[AnyHttpUrl]
    next_page: Optional[AnyHttpUrl]
    total_pages: int
    total_items: int
