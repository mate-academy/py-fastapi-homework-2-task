from datetime import date

from pydantic import BaseModel, Field, constr, conlist, condecimal, validator, confloat
from decimal import Decimal
from typing import List, Optional
from enum import Enum


class MovieRead(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieRead]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieRead):
    pass


class MovieListItemSchema(BaseModel):
    pass


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        from_attributes = True


class NamedEntitySchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieCreateSchema(BaseModel):
    name: constr(max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: condecimal(ge=0, max_digits=15, decimal_places=2)
    revenue: float = Field(..., ge=0)
    country: constr(min_length=3, max_length=3)
    genres: conlist(str, min_length=1)
    actors: conlist(str, min_length=1)
    languages: conlist(str, min_length=1)

    @validator('date')
    def date_not_too_far(cls, value):
        from datetime import timedelta, date as dt
        if value > dt.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return value


class MovieReadSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[NamedEntitySchema]
    actors: List[NamedEntitySchema]
    languages: List[NamedEntitySchema]

    class Config:
        from_attributes = True


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[confloat(ge=0, le=100)] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[confloat(ge=0)] = None
    revenue: Optional[confloat(ge=0)] = None
