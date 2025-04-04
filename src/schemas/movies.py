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

