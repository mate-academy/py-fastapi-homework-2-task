from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class ActorSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0.0)
    revenue: float = Field(ge=0.0)
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]
    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(MovieDetailSchema):
    country: str = Field(
        ..., pattern="^[A-Z]{3}$", description="ISO 3166-1 alpha-3 code"
    )
    genres: list[str]
    actors: list[str]
    languages: list[str]
    model_config = ConfigDict(from_attributes=True)

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(cls, movie_date: date):
        today = date.today()
        one_year_later = today + timedelta(days=365)

        if movie_date > one_year_later:
            raise ValueError(
                "The date must not be more than one year in the future."
            )
        return movie_date


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0.0)
    revenue: Optional[float] = Field(None, ge=0.0)
    model_config = ConfigDict(from_attributes=True)
