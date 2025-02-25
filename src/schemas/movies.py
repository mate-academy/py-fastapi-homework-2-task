import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None


class GenreResponseSchema(BaseModel):
    id: int
    name: str


class ActorResponseSchema(BaseModel):
    id: int
    name: str


class LanguageResponseSchema(BaseModel):
    id: int
    name: str


class MovieNestedListResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieNestedListResponseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    class Config:
        from_attributes = True


class MovieCreateResponseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateResponseSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(ge=0, le=100, default=None)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(ge=0, default=None)
    revenue: Optional[float] = Field(ge=0, default=None)
