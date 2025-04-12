from datetime import date, timedelta
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


# ----Detail
class CountryDetailSchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class GenreDetailSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorDetailSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageDetailSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ----Create

class CountryCreateSchema(BaseModel):
    code: str = Field(min_length=3, max_length=3)


class GenreCreateSchema(BaseModel):
    name: str


class ActorCreateSchema(BaseModel):
    name: str


class LanguageCreateSchema(BaseModel):
    name: str


class MovieListSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: CountryDetailSchema
    genres: List[GenreDetailSchema]
    actors: List[ActorDetailSchema]
    languages: List[LanguageDetailSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieCreationSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    def validate_date_not_in_future(cls, v: date):
        next_year_date = date.today() + timedelta(days=365)
        if v >= next_year_date:
            raise ValidationError("Date cannot be more than one year")
        return v

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    movies: list[MovieListSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    model_config = ConfigDict(from_attributes=True)
