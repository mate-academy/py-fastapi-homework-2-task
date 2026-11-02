from datetime import date
from typing import Optional

from database.models import MovieStatusEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CountyBase(BaseModel):
    id: int
    name: str
    code: str

class ActorBase(BaseModel):
    id: int
    name: str

class GenreBase(BaseModel):
    id: int
    name: str

class MovieBase(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country_id: int

class MovieDetailSchema(MovieBase):
    country: Optional[str] = None
    genres: list[GenreBase] = []
    actors: list[ActorBase] = []
    languages: list[CountyBase] = []

class MovieCreate(MovieBase):
    name: str  = Field(max_length=255)
    score: float = Field(lt=100, ge=0)
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country_id: int
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("event_date")
    @classmethod
    def validate_future_limit(cls, v: date) -> date:
        today = date.today()
        one_year_hence = today.replace(year=today.year + 1)

        if v > one_year_hence:
            raise ValueError(
                f"Date cannot be more than 1 year in the future. "
                f"Max allowed date: {one_year_hence}"
            )
        return v

class MovieUpdate(MovieBase):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    model_config = ConfigDict(from_attributes=True)

class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int