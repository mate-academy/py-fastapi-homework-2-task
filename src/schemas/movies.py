import datetime

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum
from schemas.actors import ActorRead
from schemas.countries import CountryRead
from schemas.genres import GenreRead
from schemas.languages import LanguageRead


class ValidateDateMixin:
    @field_validator("date", mode="after")
    @classmethod
    def check_date(cls, date: datetime.date) -> datetime.date:
        if date is not None and date > datetime.date.today() + relativedelta(years=1):
            raise ValueError("Date cannot be more than 1 year in the future.")
        return date


class MovieBase(BaseModel, ValidateDateMixin):
    name: str = Field(max_length=255, min_length=1)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(min_length=2, max_length=3)
    genres: list[str] = Field(min_length=1)
    actors: list[str] = Field(min_length=1)
    languages: list[str] = Field(min_length=1)

    @field_validator("country", mode="after")
    @classmethod
    def validate_country_code(cls, value: str) -> str:
        value = value.strip().upper()
        if value == "US":
            return "USA"
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Country code must be a valid 3-letter ISO alpha-3 code.")
        return value


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


class MoviePartialUpdate(BaseModel, ValidateDateMixin):
    name: str | None = Field(default=None, max_length=255, min_length=1)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
