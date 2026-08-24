import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


def check_not_in_future(date: datetime.date) -> datetime.date:
    if (date - datetime.date.today()).days > 365:
        raise ValueError("The date is in the future more than a year")
    return date


DateValidator = Annotated[datetime.date, AfterValidator(check_not_in_future)]


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    date: DateValidator
    score: Annotated[float, Field(ge=0.0, le=100.0)]
    overview: str
    status: MovieStatusEnum
    budget: Annotated[float, Field(ge=0.0)]
    revenue: Annotated[float, Field(ge=0.0)]
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None
    country: str | None = None
    genres: list[str] | None = None
    actors: list[str] | None = None
    languages: list[str] | None = None
