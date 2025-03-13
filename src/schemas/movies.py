from pydantic import BaseModel, constr, confloat
from datetime import date

from database.models import MovieStatusEnum


class GenreModelSchema(BaseModel):
    id: int
    name: str
    movies: list["MovieDetailSchema"]

    class Config:
        from_attributes = True


class ActorModelSchema(BaseModel):
    id: int
    name: str
    movies: list["MovieDetailSchema"]

    class Config:
        from_attributes = True


class CountryModelSchema(BaseModel):
    id: int
    code: constr(max_length=3)
    name: str
    movies: list["MovieDetailSchema"]

    class Config:
        from_attributes = True


class LanguageModelSchema(BaseModel):
    id: int
    name: str
    movies: list["MovieDetailSchema"]

    class Config:
        from_attributes = True


class MovieBaseSchema(BaseModel):
    name: str
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country_id: int

    country: "CountryModelSchema"
    genres: list["GenreModelSchema"]
    actors: list["ActorModelSchema"]
    languages: list["LanguageModelSchema"]

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: confloat(ge=0, le=100)
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_items: int
    total_pages: int

    class Config:
        from_attributes = True


class MovieDetailSchema(MovieBaseSchema):
    id: int


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    class Config:
        from_attributes = True
