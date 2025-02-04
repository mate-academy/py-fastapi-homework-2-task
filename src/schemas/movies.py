from datetime import date, timedelta
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, constr, Field, field_validator
from pydantic_extra_types.country import CountryAlpha2


class MoviesStatusEnumSchema(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class GenreResponseSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class ActorResponseSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class CountryResponseSchema(BaseModel):
    id: int
    code: CountryAlpha2
    name: Optional[str]
    model_config = {"from_attributes": True}


class LanguageResponseSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class MovieCreateResponseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MoviesStatusEnumSchema
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: CountryAlpha2
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    def validate_date_no_more_one_year(cls, movie_date: str | date):
        if isinstance(movie_date, str):
            try:
                movie_date = date.fromisoformat(movie_date)
            except ValueError:
                raise ValueError(f"Invalid date format: {movie_date}")
        if movie_date > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return movie_date


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MoviesStatusEnumSchema
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    model_config = {"from_attributes": True}


class MovieUpdateResponseSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MoviesStatusEnumSchema] = None
    budget: Optional[float] = Field(None, gt=0)
    revenue: Optional[float] = Field(None, gt=0)


class MovieListItemResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieDetailResponseSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}
