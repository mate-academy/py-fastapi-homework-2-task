from pydantic import BaseModel, Field, conlist, constr, confloat, field_validator, ConfigDict
from typing import List, Optional
from datetime import date
from enum import Enum


# ---------- ENUM ----------

class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


# ---------- ENTITY READS ----------

class EntityRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountryRead(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------- FILM SCHEMAS ----------

class FilmCreate(BaseModel):
    name: constr(max_length=255)
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: confloat(ge=0)
    revenue: confloat(ge=0)
    country: constr(min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        from datetime import timedelta, date as dt
        if value > dt.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return value


class FilmUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None  # Убрал confloat
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None  # Убрал confloat
    revenue: Optional[float] = None


class FilmRead(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryRead
    genres: List[EntityRead]
    actors: List[EntityRead]
    languages: List[EntityRead]

    model_config = ConfigDict(from_attributes=True)


class PaginatedFilmList(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
