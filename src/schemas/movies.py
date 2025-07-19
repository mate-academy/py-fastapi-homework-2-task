from pydantic import BaseModel, confloat, constr, validator
from datetime import date, datetime
from typing import List, Optional, Literal, Union
from enum import Enum

class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"

# Pagination and Movie List Schemas
class MovieListResponseItem(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        orm_mode = True

class MovieListResponseSchema(BaseModel):
    movies: List[MovieListResponseItem]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

# Country Schema
class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

# Genre/Actor/Language Schemas
class GenreResponseSchema(BaseModel):
    id: int
    name: str

class ActorResponseSchema(BaseModel):
    id: int
    name: str

class LanguageResponseSchema(BaseModel):
    id: int
    name: str

# Detailed Movie Schema
class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]

    class Config:
        orm_mode = True

# Movie Creation Schema
class MovieCreateRequestSchema(BaseModel):
    name: constr(max_length=255)
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: confloat(ge=0)
    revenue: confloat(ge=0)
    country: constr(min_length=3, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @validator('date')
    def validate_date(cls, value):
        max_date = date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError('Date cannot be more than one year in the future')
        return value

# Movie Update Schema
class MovieUpdateRequestSchema(BaseModel):
    name: Optional[constr(max_length=255)] = None
    date: Optional[date] = None
    score: Optional[confloat(ge=0, le=100)] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[confloat(ge=0)] = None
    revenue: Optional[confloat(ge=0)] = None

    @validator('date')
    def validate_date(cls, value):
        if value:
            max_date = date.today() + datetime.timedelta(days=365)
            if value > max_date:
                raise ValueError('Date cannot be more than one year in the future')
        return value
