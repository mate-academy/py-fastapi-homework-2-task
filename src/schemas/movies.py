from datetime import datetime, timedelta
from pydantic import BaseModel, condecimal, constr, Field, validator
from typing import Optional, Literal

class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

class GenreSchema(BaseModel):
    id: int
    name: str

class ActorSchema(BaseModel):
    id: int
    name: str

class LanguageSchema(BaseModel):
    id: int
    name: str

class MovieBase(BaseModel):
    name: constr(max_length=255)
    date: str
    score: float = Field(..., ge=0, le=100)
    overview: str

    @validator("date")
    def validate_date(cls, value: str) -> str:
        date_value = datetime.strptime(value, "%Y-%m-%d").date()
        max_allowed = datetime.now().date() + timedelta(days=365)
        if date_value > max_allowed:
            raise ValueError("The release date cannot be more than one year in the future.")
        return value

class Movie(MovieBase):
    id: int

class MovieCreate(MovieBase):
    status: Literal["Released", "Post Production", "In Production"]
    budget: condecimal(ge=0)
    revenue: condecimal(ge=0)
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

class MovieUpdate(BaseModel):
    name: Optional[constr(max_length=255)] = None
    date: Optional[str] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[Literal["Released", "Post Production", "In Production"]] = None
    budget: Optional[condecimal(ge=0)] = None
    revenue: Optional[condecimal(ge=0)] = None


class MovieDetailSchema(Movie):
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieListItemSchema(Movie):
    status: Literal["Released", "Post Production", "In Production"]
    score: float


class MovieListResponseSchema(BaseModel):
    movies: list[Movie]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
