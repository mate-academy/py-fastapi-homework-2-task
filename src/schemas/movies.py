import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic_extra_types.country import CountryAlpha2
from schemas.actors import ActorListItemSchema
from schemas.countries import CountryListItemSchema
from schemas.genres import GenreListItemSchema
from schemas.languages import LanguageListItemSchema


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str = Field(min_length=1)
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryAlpha2
    genres: list[str] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    @field_validator("date")
    @classmethod
    def validate_date_not_more_than_one_year_future(cls, value: datetime.date):
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future")
        return value


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryListItemSchema
    genres: list[GenreListItemSchema]
    actors: list[ActorListItemSchema]
    languages: list[LanguageListItemSchema]


class MovieUpdateSchema(BaseModel):

    name: str | None = Field(default=None, min_length=1, max_length=255)
    date: datetime.date | None = None
    score: float = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float = Field(default=None, ge=0)
    revenue: float = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date_not_more_than_one_year_future(
        cls, value: datetime.date | None
    ) -> datetime.date | None:
        if value and value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future")
        return value
