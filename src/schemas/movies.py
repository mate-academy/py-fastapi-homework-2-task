from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from database.models import MovieStatusEnum


class MovieSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class PaginatedMovieResponseSchema(BaseModel):
    movies: list[MovieSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CreateMovieSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class BaseSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CountrySchema(BaseSchema):
    code: str
    name: Optional[str]


class GenreSchema(BaseSchema):
    pass


class ActorSchema(BaseSchema):
    pass


class LanguageSchema(BaseSchema):
    pass


class CreateResponseMovieSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    class Config:
        from_attributes = True


class MovieDetailSchema(CreateResponseMovieSchema):
    pass


class UpdateMovieRequest(BaseModel):
    name: str = None
    date: str = None
    score: float = None
    overview: str = None
    status: str = None
    budget: float = None
    revenue: float = None
