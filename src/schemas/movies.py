from typing import List, Optional

from pydantic import BaseModel
from datetime import date
from database.models import MovieStatusEnum

class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class GenreItemSchema(BaseModel):
    id: int
    name: str


class ActorItemSchema(GenreItemSchema):
    pass


class LanguageItemSchema(GenreItemSchema):
    pass


class CountryItemSchema(BaseModel):
    id: int
    code: str
    name: str | None = None


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None


class MovieDetailSchema(MovieCreateSchema):
    id: int
    country: CountryItemSchema
    genres: List[GenreItemSchema]
    actors: List[ActorItemSchema]
    languages: List[LanguageItemSchema]
