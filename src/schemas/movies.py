from datetime import datetime

from pydantic import BaseModel


class MovieSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country_id: int
    country: str
    genres: list[dict]
    actors: list[dict]
    languages: list[dict]

    class Config:
        from_attributes = True


class MovieList(MovieSchema):
    page: int
    prev_page: int | None = None
    next_page: int | None = None


class MovieDetail(MovieSchema):
    pass

