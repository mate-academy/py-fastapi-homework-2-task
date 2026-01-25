import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic_extra_types.country import CountryAlpha3

from database.models import MovieStatusEnum


class MovieBaseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float = Field(le=100, ge=0)
    overview: str


class MovieDetailSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    movies: list[MovieDetailSchema]
    prev_page: None | str
    next_page: None | str
    total_pages: int
    total_items: int


class MovieInputCreateSchema(MovieBaseSchema):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryAlpha3
    genres: list[str]
    actors: list[str]
    languages: list[str]


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str | None


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MovieOutputCreateSchema(MovieBaseSchema):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]
    id: int


class MovieRetrieveSchema(MovieOutputCreateSchema):
    pass


class MovieUpdateSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = Field(None, le=100, ge=0)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float = Field(None, ge=0)
