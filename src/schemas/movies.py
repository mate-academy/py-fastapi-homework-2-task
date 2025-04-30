from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class CountrySchema(BaseModel):
    country_id: int
    code: str
    name: Optional[str] = None

    model_config = {"from_attributes": True}


class GenreSchema(BaseModel):
    genre_id: int
    name: str

    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    actor_id: int
    name: str

    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    language_id: int
    name: str

    model_config = {"from_attributes": True}


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
    movie_id: int
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

    model_config = {"from_attributes": True}


class MovieSchema(MovieResponseSchema):
    pass


class MoviesListResponse(BaseModel):
    movies: List[MovieSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieShortSchema(BaseModel):
    movie_id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}
