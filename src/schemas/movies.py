from datetime import date, timedelta
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationError
)
from pydantic_extra_types.country import CountryAlpha3, CountryAlpha2


class CountrySchema(BaseModel):
    id: int
    code: CountryAlpha3 | CountryAlpha2
    name: str | None


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str


class StatusEnum(str, Enum):
    Released = "Released"
    PostProduction = "Post Production"
    InProduction = "In Production"


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: StatusEnum
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: CountryAlpha3 | CountryAlpha2
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    def parse_and_validate_date(cls, movie_date: str | date):
        if isinstance(movie_date, str):
            try:
                movie_date = date.fromisoformat(movie_date)
            except ValueError:
                raise ValueError(f"Invalid date format: {movie_date}")
        if movie_date > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return movie_date


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: StatusEnum
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    class Config:
        from_attributes = True


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[StatusEnum] = None
    budget: Optional[float] = Field(None, gt=0)
    revenue: Optional[float] = Field(None, gt=0)


class MovieListSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True
