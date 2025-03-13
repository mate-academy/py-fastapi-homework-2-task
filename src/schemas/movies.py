from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Optional
from datetime import date, timedelta
from database.models import MovieStatusEnum


class GenreBase(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class ActorBase(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class CountryBase(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {
        "from_attributes": True,
    }


class LanguageBase(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryBase
    genres: List[GenreBase]
    actors: List[ActorBase]
    languages: List[LanguageBase]

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
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

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }
