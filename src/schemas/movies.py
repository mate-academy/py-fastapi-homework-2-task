from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class GenreModel(BaseModel):
    name: str
    movies: list["MovieDetailSchema"]


class GenreDetail(GenreModel):
    id: int

    class Config:
        from_attributes = True


class GenreDetailResponse(BaseModel):
    id: int
    name: str


class ActorModel(BaseModel):
    name: str
    movies: list["MovieDetailSchema"]


class ActorDetail(ActorModel):
    id: int

    class Config:
        from_attributes = True


class ActorDetailResponse(BaseModel):
    id: int
    name: str


class CountryModel(BaseModel):
    code: str
    name: Optional[str] = None
    movies: list["MovieDetailSchema"]


class CountryDetail(CountryModel):
    int: int

    class Config:
        from_attributes = True


class CountryDetailResponse(BaseModel):
    id: int
    code: str
    name: Optional[str] = None


class LanguageModel(BaseModel):
    name: str
    movies: list["MovieDetailSchema"]


class LanguageDetail(LanguageModel):
    int: int

    class Config:
        from_attributes = True


class LanguageDetailResponse(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    name: str
    date: date
    score: float = Field(ge=0, le=100, description="Score value must be between 0 and 100")
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0, description="Budget must be greater than or equal to 0")
    revenue: float = Field(ge=0, description="Revenue must be greater than or equal to 0")
    country_id: int
    country: CountryDetail
    genres: list["GenreDetail"]
    actors: list["ActorDetail"]
    languages: list["LanguageDetail"]

