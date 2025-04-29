from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        orm_mode = True


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        orm_mode = True


class MovieSchema(MovieResponseSchema):
    pass  # Спадковується для сумісності в MoviesListResponse


class MoviesListResponse(BaseModel):
    movies: List[MovieSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
