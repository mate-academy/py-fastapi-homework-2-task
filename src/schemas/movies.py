import datetime

from pydantic import BaseModel, ConfigDict

from database.models import MovieStatusEnum


class MovieBase(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    revenue: float
    country_id: int


class MovieBaseRead(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    movies: list[MovieBaseRead]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
