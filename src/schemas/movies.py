from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum, CountryModel, GenreModel, ActorModel, LanguageModel


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


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    # country_id: int
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: str #=Field(max_length=255)
    date: date
    score: float #=Field(gt=0, lt=100)
    overview: str
    status: MovieStatusEnum
    budget: float #=Field(ge=0)
    revenue: float #=Field(ge=0)

    # country_id: int
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: Optional[str] = None  #=Field(max_length=255)
    date: Optional[date] = None
    score: Optional[float] = None  #=Field(gt=0, lt=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None  #=Field(ge=0)
    revenue: Optional[float] = None   #=Field(ge=0)


class MovieListSchema(BaseModel):
    model_config  = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


# class FilmCreate(FilmBase):
#     pass
#
# class FilmUpdate(FilmBase):
#     pass
#
# class FilmRead(FilmBase):
#     id: int
#
#     class Config:
#         from_attributes = True
