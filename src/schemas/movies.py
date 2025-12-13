import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponse(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class RelatedItemSchema(BaseModel):
    id: int
    name: str


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[RelatedItemSchema]
    actors: List[RelatedItemSchema]
    languages: List[RelatedItemSchema]


class MovieCreateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[str] = Field(None, max_length=3)
    genres: List[str] = Field(default_factory=list)
    actors: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
