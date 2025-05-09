from datetime import date, timedelta
from typing import Optional, List, Annotated

from pydantic import BaseModel, Field, field_validator


class CountrySchema(BaseModel):
    id: int
    code: Annotated[str, Field(pattern="^[A-Z]{3}$")]
    name: str | None

    model_config = {
        "from_attributes": True,
    }


class GenresListSchema(BaseModel):
    id: int
    name: str


class ActorsListSchema(BaseModel):
    id: int
    name: str


class LanguagesListSchema(BaseModel):
    id: int
    name: str


class BaseMoviesSchema(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    date: Annotated[date, Field()]
    score: Annotated[float, Field(ge=0, le=100)]
    overview: str
    status: Annotated[str, Field(pattern="^(Released|Post Production|In Production)$")]
    budget: Annotated[float, Field(ge=0)]
    revenue: Annotated[float, Field(ge=0)]

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far(cls, value: date) -> date:
        max_allowed = date.today() + timedelta(days=365)
        if value > max_allowed:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieDetailSchema(BaseMoviesSchema):
    id: int
    country: CountrySchema
    genres: Annotated[list[GenresListSchema], Field(min_length=1)]
    actors: Annotated[list[ActorsListSchema], Field(min_length=1)]
    languages: Annotated[list[LanguagesListSchema], Field(min_length=1)]

    model_config = {
        "from_attributes": True,
    }


class MovieCreateSchema(BaseMoviesSchema):
    country: str
    genres: Annotated[list[str], Field(min_length=1)]
    actors: Annotated[list[str], Field(min_length=1)]
    languages: Annotated[list[str], Field(min_length=1)]

    model_config = {
        "from_attributes": True,
    }


class MoviePatchSchema(MovieCreateSchema):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(Released|Post Production|In Production)$")
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
    country: Optional[str] = None
    genres: Optional[list[str]] = None
    actors: Optional[list[str]] = None
    languages: Optional[list[str]] = None

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far(cls, value: date) -> date:
        max_allowed = date.today() + timedelta(days=365)
        if value > max_allowed:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MoviesListSchema(BaseModel):
    movies: List[MovieDetailSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
    }
