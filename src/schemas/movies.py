import datetime
import enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date_not_too_future(cls, value: datetime.date):
        one_year_ahead = datetime.date.today() + datetime.timedelta(days=365)
        if value > one_year_ahead:
            raise ValueError("Release date cannot be more than one year in the future.")
        return value


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date_not_too_future(cls, value: datetime.date):
        one_year_ahead = datetime.date.today() + datetime.timedelta(days=365)
        if value > one_year_ahead:
            raise ValueError("Release date cannot be more than one year in the future.")
        return value
