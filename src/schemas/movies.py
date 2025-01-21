import datetime
from datetime import timedelta
from typing import Annotated, Optional, List, Any

from fastapi import HTTPException

from pydantic import BaseModel, model_validator, ConfigDict, Field

from database.models import ActorModel, GenreModel, LanguageModel, MovieStatusEnum


class MovieModelSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListSchema(BaseModel):
    movies: list[MovieModelSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field(le=datetime.date.today() + timedelta(days=365))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(description="ISO 3166-1 alpha-3 code")
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True


class MovieResponseSchema(MovieCreateSchema):
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieDetailSchema(MovieModelSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieDeleteSchema(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
