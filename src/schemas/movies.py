import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum
from schemas import references


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = ConfigDict(from_attributes=True)


class MovieCreateResponseSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: references.Country
    genres: list[references.Genre]
    actors: list[references.Actor]
    languages: list[references.Language]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
