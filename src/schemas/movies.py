import datetime
from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class MovieStatus(StrEnum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    genre: str
    overview: str
    crew: str
    orig_title: str
    status: str
    orig_lang: str
    budget: float
    revenue: float
    country: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieDetailResponseSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateResponseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateResponseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
