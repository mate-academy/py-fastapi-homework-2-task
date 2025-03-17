from datetime import date as datetime_date
from enum import Enum

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, ConfigDict
from pydantic_extra_types.country import CountryAlpha3, CountryAlpha2

from schemas.base import RelatedObjectBaseSchema
from schemas.countries import CountrySchema


class MovieStatusEnum(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime_date = Field(le=datetime_date.today() + relativedelta(years=1))
    score: float = Field(ge=0.0, le=100.0)
    overview: str


class MovieCreateSchema(MovieBaseSchema):
    budget: float = Field(ge=0.0)
    revenue: float = Field(ge=0.0)
    status: MovieStatusEnum
    country: CountryAlpha3 | CountryAlpha2
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(max_length=255, default=None)
    date: datetime_date | None = Field(le=datetime_date.today() + relativedelta(years=1), default=None)
    score: float | None = Field(ge=0.0, le=100.0, default=None)
    overview: str | None = None
    budget: float | None = Field(ge=0.0, default=None)
    revenue: float | None = Field(ge=0.0, default=None)
    status: MovieStatusEnum | None = None


class MovieDetailSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    budget: float
    revenue: float
    status: MovieStatusEnum
    country: CountrySchema
    genres: list[RelatedObjectBaseSchema]
    actors: list[RelatedObjectBaseSchema]
    languages: list[RelatedObjectBaseSchema]


class MovieListItemSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
