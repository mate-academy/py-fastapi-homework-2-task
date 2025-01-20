import datetime
from datetime import timedelta
from typing import Optional
from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class GenreReadSchema(BaseModel):
    id: int
    name: str


class ActorReadSchema(BaseModel):
    id: int
    name: str


class LanguageReadSchema(BaseModel):
    id: int
    name: str


class MovieReadResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieReadResponseSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field(le=datetime.date.today() + timedelta(days=365))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(description="ISO 3166-1 alpha-3 code")
    genres: list[str]
    actors: list[str]
    languages: list[str]

    class Config:
        from_attributes = True


class MovieResponseSchema(MovieCreateSchema):
    country: CountryResponseSchema
    genres: list[GenreReadSchema]
    actors: list[ActorReadSchema]
    languages: list[LanguageReadSchema]

class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenreReadSchema]
    actors: list[ActorReadSchema]
    languages: list[LanguageReadSchema]

    model_config = {"from_attributes": True}


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = Field(None, le=datetime.date.today() + timedelta(days=365))
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
