from datetime import date as date_type
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, ConfigDict
from database.models import MovieStatusEnum


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: date_type = Field(le=date_type.today() + relativedelta(years=1))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)


class MovieListItemSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: date_type = Field(le=date_type.today() + relativedelta(years=1))
    score: float = Field(ge=0, le=100)
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateItemSchema(MovieBase):
    country: str = Field(max_length=3, description="ISO 3166-1 alpha-3 code")
    genres: list[str]
    actors: list[str]
    languages: list[str]


class CountryDetailSchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class GenresDetailSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorsDetailSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguagesDetailSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieBase):
    id: int
    country: CountryDetailSchema
    genres: list[GenresDetailSchema]
    actors: list[ActorsDetailSchema]
    languages: list[LanguagesDetailSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(MovieBase):
    name: str | None = None
    score: float | None = None
    date: date_type | None = None
    overview: str | None = None
    status: str | None = None
    budget: float | None = None
    revenue: float | None = None
