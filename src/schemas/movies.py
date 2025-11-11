from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from schemas.countries import CountrySchema


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str] = None

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str]
    status: str
    budget: float
    revenue: Optional[float]
    country: Optional[CountrySchema]
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        from_attributes = True


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: Optional[str]
    status: str
    budget: float
    revenue: Optional[float]
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
