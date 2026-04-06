import pycountry
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date
from database.models import MovieStatusEnum

"""
I understand that there is duplication of code here,
but it is easier to read it this way,
since there is not much written.
"""


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    # The database uses alpha-2 country codes,
    # so it was decided to use that instead of what is stated in the README.md
    @field_validator("country")
    @classmethod
    def validate_country(cls, value):
        if not pycountry.countries.get(alpha_2=value):
            raise ValueError(f"Invalid country code: {value}")
        return value

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        if value.year > date.today().year + 1:
            raise ValueError(f"Invalid date: {value}")
        return value


class DefaultRelatedSchema(BaseModel):
    id: int
    name: str


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[DefaultRelatedSchema]
    actors: List[DefaultRelatedSchema]
    languages: List[DefaultRelatedSchema]


class MoviePatchSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        if value.year > date.today().year + 1:
            raise ValueError(f"Invalid date: {value}")
        return value
