import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum
from schemas.actors import ActorDetailSchema
from schemas.countries import CountryDetailSchema
from schemas.genres import GenreDetailSchema
from schemas.languages import LanguageDetailSchema


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieListItemSchema):
    status: str
    budget: float
    revenue: float
    country: CountryDetailSchema
    genres: List[GenreDetailSchema]
    actors: List[ActorDetailSchema]
    languages: List[LanguageDetailSchema]


class MovieCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=3, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: datetime.date) -> datetime.date:
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if v > max_date:
            raise ValueError("Date must not be more than one year in the future.")
        return v
