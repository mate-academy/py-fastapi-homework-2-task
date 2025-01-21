import datetime

from pydantic import BaseModel

from database.models import (
    MovieStatusEnum,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)


class MovieSchemaBase(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None


class MovieSchema(MovieSchemaBase):
    id: int

    class Config:
        from_attributes = True


class MovieListSchema(BaseModel):
    movies: list[MovieSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class CountrySchemaResponse(BaseModel):
    id: int
    code: str
    name: str | None


class GenreSchemaResponse(BaseModel):
    id: int
    name: str


class ActorSchemaResponse(BaseModel):
    id: int
    name: str


class LanguageSchemaResponse(BaseModel):
    id: int
    name: str


class MovieBaseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float


class MovieCreateRequest(MovieBaseSchema):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieCreateResponse(MovieBaseSchema):
    id: int
    country: CountrySchemaResponse
    genres: list[GenreSchemaResponse]
    actors: list[ActorSchemaResponse]
    languages: list[LanguageSchemaResponse]

    class Config:
        from_attributes = True


class MovieUpdate(MovieSchemaBase):
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None

    class Config:
        from_attributes = True
