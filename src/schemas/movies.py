from typing import Optional

import pycountry
from pydantic import BaseModel, Field, field_validator, validator, constr, confloat
from enum import Enum
from pydantic_extra_types.country import CountryAlpha3
from datetime import date


class StatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class CountryBase(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {
        "from_attributes": True
    }


class GenreBase(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class ActorBase(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class LanguageBase(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class MovieBase(BaseModel):
    name: str
    date: date
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: str


class MovieFullBase(MovieBase):
    status: StatusEnum
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
    country: CountryBase
    genres: list[GenreBase]
    actors: list[ActorBase]
    languages: list[LanguageBase]


class MovieSummary(BaseModel):
    id: int
    name: str
    date: date
    score: Optional[float]
    overview: str

    class Config:
        from_attributes = True


class MovieList(BaseModel):
    movies: list[MovieSummary]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreate(BaseModel):
    name: constr(max_length=255)
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: StatusEnum
    budget: confloat(ge=0)
    revenue: confloat(ge=0)
    country: constr(min_length=2, max_length=3)  # ISO alpha-3
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def check_date_not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[StatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def check_date_not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class MovieRead(MovieFullBase):
    id: int

    class Config:
        from_attributes = True
