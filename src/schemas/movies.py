import datetime

from pydantic import BaseModel

from database.models import MovieStatusEnum


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = {"from_attributes": True}


class GenreResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class LanguageResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieListReadResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListReadResponseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    model_config = {"from_attributes": True}


class MovieCreateResponseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = {"from_attributes": True}


class MovieUpdateResponseSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None

    model_config = {"from_attributes": True}
