import datetime

from pydantic import BaseModel, Field, field_validator
from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class CountryCreateSchema(BaseModel):
    code: str
    name: str | None


class CountryCreateResponseSchema(CountryCreateSchema):
    id: int


class GenreCreateSchema(BaseModel):
    name: str


class GenreCreateResponseSchema(GenreCreateSchema):
    id: int


class ActorCreateSchema(BaseModel):
    name: str


class ActorCreateResponseSchema(ActorCreateSchema):
    id: int


class LanguageCreateSchema(BaseModel):
    name: str


class LanguageCreateResponseSchema(LanguageCreateSchema):
    id: int


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float = Field(default=0, ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate(cls, value: datetime.date) -> datetime.date:
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future")
        return value


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryCreateResponseSchema
    genres: list[GenreCreateResponseSchema]
    actors: list[ActorCreateResponseSchema]
    languages: list[LanguageCreateResponseSchema]


class MovieDetailSchema(MovieCreateResponseSchema):
    pass


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date | None):
        if value is None:
            return value
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future")
        return value
