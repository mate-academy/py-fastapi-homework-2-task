import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic_extra_types.country import CountryAlpha3, CountryAlpha2

from database.models import MovieStatusEnum
from schemas.actors import ActorScheme
from schemas.countries import CountryScheme
from schemas.genres import GenreScheme
from schemas.languages import LanguageScheme


class MovieBaseScheme(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str


class MovieBaseExtendedScheme(MovieBaseScheme):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)


class MovieListItemSchema(MovieBaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: None | str = None
    next_page: None | str = None
    total_pages: int
    total_items: int


class MovieCreateScheme(MovieBaseExtendedScheme):
    country: CountryAlpha3 | CountryAlpha2
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(cls, value: datetime.date) -> datetime.date:
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError(
                "Date must not be more than one year in the future."
            )
        return value


class MovieDetailSchema(MovieBaseExtendedScheme):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: CountryScheme
    genres: list[GenreScheme]
    actors: list[ActorScheme]
    languages: list[LanguageScheme]


class MovieUpdateScheme(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
