import datetime

from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


class CountryBaseSchema(BaseModel):
    code: str
    name: str | None = None


class CountryDetailSchema(CountryBaseSchema):
    id: int


class GenreBaseSchema(BaseModel):
    name: str


class GenreDetailSchema(GenreBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ActorBaseSchema(BaseModel):
    name: str


class ActorDetailSchema(ActorBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LanguageBaseSchema(BaseModel):
    name: str


class LanguageDetailSchema(LanguageBaseSchema):
    id: int


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class MovieCreateItemSchema(BaseModel):
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryDetailSchema
    genres: list[GenreDetailSchema]
    actors: list[ActorDetailSchema]
    languages: list[LanguageDetailSchema]


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
