from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, timedelta, datetime

from pydantic.v1 import validator, constr

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    name: Optional[str]  # ← тимчасово, поки не очистиш NULL-и в БД

    class Config:
        from_attributes = True


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieCreateResponseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country_id: Optional[int]
    country_name: Optional[str]  # дозволяємо створити нову країну
    genre_ids: List[int] = []
    genre_names: List[str] = []
    actor_ids: List[int] = []
    actor_names: List[str] = []
    language_ids: List[int] = []
    language_names: List[str] = []

    @validator("date")
    def check_date_not_too_far(cls, v):
        if v > date.today() + timedelta(days=365):
            raise ValueError("Release date must not be more than one year in the future")
        return v


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        from_attributes = True


class MovieDetailListSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieDetailListSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[constr(max_length=255)]
    date: Optional[date]
    score: Optional[float]
    overview: Optional[str]
    status: Optional[str]
    budget: Optional[float]
    revenue: Optional[float]
