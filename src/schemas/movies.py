import datetime
from typing import List, Optional

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None


class GenreResponseSchema(BaseModel):
    id: int
    name: str


class ActorResponseSchema(BaseModel):
    id: int
    name: str


class LanguageResponseSchema(BaseModel):
    id: int
    name: str


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def date_validation(cls, date: datetime.date | None):
        if date is not None:
            if date > datetime.date.today() + datetime.timedelta(days=365):
                raise RequestValidationError
            return date


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @field_validator("name")
    @classmethod
    def name_validation(cls, name: str | None):
        if name is not None:
            if len(name) > 255:
                raise RequestValidationError
            return name

    @field_validator("date")
    @classmethod
    def date_validation(cls, date: datetime.date | None):
        if date is not None:
            if date > datetime.date.today() + datetime.timedelta(days=365):
                raise RequestValidationError
            return date

    @field_validator("score")
    @classmethod
    def score_validation(cls, score: float | None):
        if score is not None:
            if not (score >= 0 and score <= 100):
                raise RequestValidationError
            return score

    @field_validator("budget")
    @classmethod
    def budget_validation(cls, budget: float | None):
        if budget is not None:
            if not budget >= 0:
                raise RequestValidationError
            return budget

    @field_validator("revenue")
    @classmethod
    def revenue_validation(cls, revenue: float | None):
        if revenue is not None:
            if not revenue >= 0:
                raise RequestValidationError
            return revenue
