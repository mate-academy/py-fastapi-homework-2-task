from datetime import date
from typing import Annotated
from dateutil.relativedelta import relativedelta

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class CountryListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    code: str


class GenreListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


def validate_max_one_year_future(value: date) -> date:
    max_date = date.today() + relativedelta(years=1)

    if value > max_date:
        raise ValueError(
            f"Date cannot be further than 1 year in the future (Max allowed: {max_date})"
        )
    return value


FutureMaxOneYearDate = Annotated[date, AfterValidator(validate_max_one_year_future)]


class MovieCreateSchema(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    date: FutureMaxOneYearDate
    score: Annotated[float, Field(ge=0, le=100)]
    overview: str
    status: MovieStatusEnum
    budget: Annotated[float, Field(ge=0)]
    revenue: Annotated[float, Field(ge=0)]
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MoviePatchSchema(BaseModel):
    name: Annotated[str, Field(max_length=255)] | None = None
    date: FutureMaxOneYearDate | None = None
    score: Annotated[float, Field(ge=0, le=100)] | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: Annotated[float, Field(ge=0)] | None = None
    revenue: Annotated[float, Field(ge=0)] | None = None


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryListResponseSchema
    genres: list[GenreListResponseSchema]
    actors: list[ActorListResponseSchema]
    languages: list[LanguageListResponseSchema]
