from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = {"from_attributes": True}


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class BaseMovie(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)


class MovieDetailSchema(BaseMovie):
    id: int
    country_id: int

    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = {"from_attributes": True}

    @field_validator("date")
    def validate_data(cls, value: date) -> date:
        current_year = datetime.now().year
        if value.year > current_year + 1:
            raise ValueError(
                f"The year in 'date' cannot be greater "
                f"than {current_year + 1}."
            )
        return value


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseMovie):
    country: str = Field(..., max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = {"from_attributes": True}

    @field_validator("date")
    def validate_data(cls, value: date) -> date:
        current_year = datetime.now().year
        if value.year > current_year + 1:
            raise ValueError(
                f"The year in 'date' cannot be greater "
                f"than {current_year + 1}."
            )
        return value


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: Optional[date] = None
    score: float | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None

    model_config = {"from_attributes": True}
