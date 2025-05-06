import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum


class GenreResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CountryResponse(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = {"from_attributes": True}


class LanguageResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(min_length=2, max_length=2)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: datetime.date) -> datetime.date:
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError(
                "The date must not be more than one year in the future."
            )
        return value

    model_config = {"from_attributes": True}


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponse
    genres: list[GenreResponse]
    actors: list[ActorResponse]
    languages: list[LanguageResponse]

    model_config = {"from_attributes": True}


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: datetime.date) -> datetime.date:
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError(
                "The date must not be more than one year in the future."
            )
        return value

    model_config = {"from_attributes": True}
