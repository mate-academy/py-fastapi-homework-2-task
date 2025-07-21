import datetime
from typing import Generic, TypeVar, List, Optional

from pydantic import BaseModel, ConfigDict, AnyHttpUrl

from database.models import MovieStatusEnum

M = TypeVar("M")


class IdNameBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CountryReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str]


class GenreReadSchema(IdNameBaseSchema):
    pass


class ActorReadSchema(IdNameBaseSchema):
    pass


class LanguageReadSchema(IdNameBaseSchema):
    pass


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel, Generic[M]):
    movies: List[M]
    prev_page: Optional[AnyHttpUrl]
    next_page: Optional[AnyHttpUrl]
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryReadSchema
    genres: list[GenreReadSchema]
    actors: list[ActorReadSchema]
    languages: list[LanguageReadSchema]
