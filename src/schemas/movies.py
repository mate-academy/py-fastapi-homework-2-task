from typing import List, Optional

from pydantic import BaseModel
import datetime

from database import MovieStatusEnum, CountryModel, GenreModel, ActorModel, MovieModel, LanguageModel


class MovieSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None


class LanguageSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class GenreSchema(BaseModel):
    id: int
    name: str


class MovieListItemSchema(MovieSchema):
    id: int


class MovieCreate(MovieSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    class Config:
        from_attributes = True


class MovieDetailSchema(MovieSchema):
    id: int
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema] = []
    actors: List[ActorSchema] = []
    languages: List[LanguageSchema] = []


class MovieListResponseSchema(MovieSchema):
    id: int
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class PaginationResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
