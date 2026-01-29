from typing import Optional
from datetime import date, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str]


class GenresSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguagesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def check_date(cls, value: date) -> date:
        today = date.today()
        one_year_from_now = today + timedelta(days=365)

        if value > one_year_from_now:
            raise ValueError("The date must not be more than one year in the future")
        return value


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenresSchema]
    actors: list[ActorsSchema]
    languages: list[LanguagesSchema]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def check_date(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return None

        today = date.today()
        one_year_from_now = today + timedelta(days=365)

        if value > one_year_from_now:
            raise ValueError("The date must not be more than one year in the future")
        return value
