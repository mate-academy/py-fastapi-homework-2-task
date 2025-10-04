import datetime
import enum

from pydantic import BaseModel, ConfigDict

from schemas.actors import ActorSchema
from schemas.countries import CountrySchema
from schemas.genres import GenreSchema
from schemas.languages import LanguageSchema


class MovieStatusEnum(str, enum.Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int
