from pydantic import BaseModel, ConfigDict, Field, field_validator
import datetime
from typing import Optional
from src.database.models import MovieStatusEnum


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: list[str] = []
    actors: list[str] = []
    languages: list[str] = []

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(cls, v: datetime.date) -> datetime.date:
        today = datetime.date.today()
        max_allowed = today + datetime.timedelta(days=365)
        if v > max_allowed:
            raise ValueError("date must not be more than one year in the future")
        return v


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(
        cls, v: datetime.date | None
    ) -> datetime.date | None:
        if v is None:
            return v
        today = datetime.date.today()
        max_allowed = today + datetime.timedelta(days=365)
        if v > max_allowed:
            raise ValueError("date must not be more than one year in the future")
        return v


class CountrySchema(BaseModel):
    id: int | None
    code: str
    name: str | None


class GenreSchema(BaseModel):
    id: int | None
    name: str


class ActorSchema(BaseModel):
    id: int | None
    name: str


class LanguageSchema(BaseModel):
    id: int | None
    name: str


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)
