from datetime import date as date_type
from pydantic import BaseModel, confloat

from database.models import MovieStatusEnum


class CountryDetailSchema(BaseModel):
    id: int  # noqa: VNE003
    code: str
    name: str | None

    class Config:
        from_attributes = True


class ActorDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class GenreDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieBase(BaseModel):
    name: str
    date: date_type
    score: float
    overview: str


class MovieDetailSchema(MovieBase):
    id: int  # noqa: VNE003
    status: str
    budget: float
    revenue: float
    country: CountryDetailSchema
    genres: list[GenreDetailSchema]
    actors: list[ActorDetailSchema]
    languages: list[LanguageDetailSchema]

    class Config:
        from_attributes = True


class MovieCreateSchema(MovieBase):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(MovieBase):
    name: str | None = None
    date: date_type | None = None
    # score: confloat(ge=0.0, le=100.0) | None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    # budget: confloat(ge=0.0) | None
    # revenue: confloat(ge=0.0) | None
    score: float | None = None
    budget: float | None = None
    revenue: float | None = None


class MovieListItemSchema(MovieBase):
    id: int  # noqa: VNE003

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int
