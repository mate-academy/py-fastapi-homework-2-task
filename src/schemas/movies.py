from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


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


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Optional[CountrySchema] = None
    genres: List[GenreSchema] = []
    actors: List[ActorSchema] = []
    languages: List[LanguageSchema] = []

    class Config:
        from_attributes = True


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Optional[str] = None
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
