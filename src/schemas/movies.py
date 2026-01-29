import datetime

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum
from schemas.actors import ActorBaseSchema
from schemas.countries import CountryBaseSchema
from exceptions import DateToFarException
from schemas.genres import GenreBaseSchema
from schemas.languages import LanguageBaseSchema


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field()
    score: float = Field(ge=0, le=100)
    overview: str

    @field_validator("date")
    @classmethod
    def date_not_too_far(cls, value: datetime.date) -> datetime.date:
        today = datetime.date.today()
        max_date = today + datetime.timedelta(days=365)

        if value > max_date:
            raise DateToFarException(
                "Date must not be more than one year in the future")
        return value


class MovieDetailResponseSchema(MovieBase):
    id: int

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieDetailResponseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(MovieBase):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieCreateResponseSchema(MovieBase):
    id: int
    status: str
    budget: float
    revenue: float
    country: CountryBaseSchema
    genres: list[GenreBaseSchema]
    actors: list[ActorBaseSchema]
    languages: list[LanguageBaseSchema]


class MovieUpdateRequestSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
