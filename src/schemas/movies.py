import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, NonNegativeFloat

from database.models import MovieStatusEnum


def check_release_date(value: datetime.date) -> datetime.date:
    if value > datetime.date.today() + datetime.timedelta(days=365):
        raise ValueError("The date must not be more than one year in the future.")
    return value


ReleaseDate = Annotated[datetime.date, AfterValidator(check_release_date)]


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class NamedEntitySchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(NamedEntitySchema):
    pass


class ActorSchema(NamedEntitySchema):
    pass


class LanguageSchema(NamedEntitySchema):
    pass


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
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


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: ReleaseDate
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: NonNegativeFloat
    revenue: NonNegativeFloat
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: ReleaseDate | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: NonNegativeFloat | None = None
    revenue: NonNegativeFloat | None = None
