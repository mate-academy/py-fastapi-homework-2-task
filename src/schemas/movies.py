from datetime import date, timedelta
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, ConfigDict

from database.models import MovieStatusEnum


class CountryBase(BaseModel):
    id: int
    code: str
    name: str | None


class GenreBase(BaseModel):
    id: int
    name: str


class ActorBase(BaseModel):
    id: int
    name: str


class LanguageBase(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    id: int
    name: str = Field(max_length=255, description="Length can not be more than 255")
    date: date
    score: float = Field(ge=0, le=100, description="Must be in range 0-100")
    overview: str

    @field_validator("date")
    @staticmethod
    def validate_date(value):
        if value > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future")
        return value

    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    movies: List[MovieBase]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetail(MovieBase):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryBase
    genres: list[GenreBase]
    actors: list[ActorBase]
    languages: list[LanguageBase]


class MovieCreate(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
