import datetime

from pydantic import BaseModel

from database.models import MovieStatusEnum


class GenreResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CountryResponse(BaseModel):
    id: int
    code: str
    name: str | None

    class Config:
        from_attributes = True


class LanguageResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponse
    genres: list[GenreResponse]
    actors: list[ActorResponse]
    languages: list[LanguageResponse]

    class Config:
        from_attributes = True
