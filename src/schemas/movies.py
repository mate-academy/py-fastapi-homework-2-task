from datetime import datetime, timedelta
from wsgiref.validate import validator

from pydantic import BaseModel, condecimal, constr, Field

from typing import Optional, Literal, Any, Self


class Movie(BaseModel):
    id: int
    name: constr(max_length=255)
    data: str
    score: float = Field(..., ge=0, le=100)
    overview: str

    @validator("data")
    def validate_data(cls, value: Any) -> Self:
        max_allowed = datetime.now().date() + timedelta(days=365)
        if value > max_allowed:
            raise ValueError("The release date cannot be more than one year in the future.")
        return value

class MovieListResponse(BaseModel):
    movies: list[Movie]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreate(Movie):
    status: Literal["Released", "Post Production", "In Production"]
    budget: condecimal(ge=0)
    revenue: condecimal(ge=0)
    country: constr(min_length=3, max_length=3)  # ISO alpha-3
    genres: list[str]
    actors: list[str]
    languages: list[str]

class CountryResponse(BaseModel):
    id: int
    code: str
    name: Optional[str]


class NamedEntity(BaseModel):
    id: int
    name: str


class MovieDetail(Movie):
    status: str
    budget: float
    revenue: float
    country: CountryResponse
    genres: list[NamedEntity]
    actors: list[NamedEntity]
    languages: list[NamedEntity]


class MovieUpdate(Movie):
    status: Literal["Released", "Post Production", "In Production"]
    budget: condecimal(ge=0)
    revenue: condecimal(ge=0)

