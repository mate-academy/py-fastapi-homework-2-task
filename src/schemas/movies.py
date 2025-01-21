import datetime

from pydantic import BaseModel, ConfigDict

from database.models import MovieStatusEnum


class GenreResponseSchema(BaseModel):
    id: int
    name: str


class ActorResponseSchema(BaseModel):
    id: int
    name: str


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None


class LanguageResponseSchema(BaseModel):
    id: int
    name: str


class MovieSchemaBase(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None


class MovieSchema(MovieSchemaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieListSchema(BaseModel):
    movies: list[MovieSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieBaseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float


class MovieCreateRequestSchema(MovieBaseSchema):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieCreateResponseSchema(MovieBaseSchema):
    id: int
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    country: CountryResponseSchema
    languages: list[LanguageResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(MovieSchemaBase):
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None

    model_config = ConfigDict(from_attributes=True)
