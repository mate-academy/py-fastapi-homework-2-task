from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, constr, condecimal, confloat, field_validator


class Country(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {"from_attributes": True}


class Genre(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class Actor(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class Language(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieBase(BaseModel):
    name: constr(max_length=255)
    date: date
    score: confloat(ge=0, le=100)
    overview: Optional[str]
    status: constr(pattern="^(Released|Post Production|In Production)$")  # ✅ здесь
    budget: condecimal(ge=0)
    revenue: condecimal(ge=0)
    country: constr(min_length=3, max_length=3)  # ISO code
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator('date')
    def date_not_more_than_one_year_in_future(cls, v):
        if v > (datetime.utcnow().date() + timedelta(days=365)):
            raise ValueError('date must not be more than one year in the future')
        return v


class MovieCreate(MovieBase):
    pass


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str]

    model_config = {"from_attributes": True}


class MovieDetailSchema(MovieListItemSchema):
    status: str
    budget: float
    revenue: float
    country: Country
    genres: List[Genre]
    actors: List[Actor]
    languages: List[Language]

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
