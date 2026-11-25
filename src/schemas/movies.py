import datetime

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum
from schemas.actors import ActorRead
from schemas.countries import CountryRead
from schemas.genres import GenreRead
from schemas.languages import LanguageRead


class MovieBase(BaseModel):
    name: str = Field(max_length=255, min_length=1)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(min_length=3, max_length=3)
    genres: list[str] = Field(min_length=1)
    actors: list[str] = Field(min_length=1)
    languages: list[str] = Field(min_length=1)

    @field_validator("date", mode="after")
    @classmethod
    def check_date(cls, date: datetime.date) -> datetime.date:
        if date > datetime.date.today() + relativedelta(years=1):
            raise ValueError("Date cannot be more than 1 year in the future.")
        return date


class MovieCreate(MovieBase):
    pass


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryRead
    genres: list[GenreRead]
    actors: list[ActorRead]
    languages: list[LanguageRead]


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
