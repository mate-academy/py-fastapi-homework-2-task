# Write your code here
import datetime
from typing import Optional

from src.database.models import MovieStatusEnum
from pydantic import BaseModel, Field, field_validator
from src.schemas.actors import ActorResponseSchema
from src.schemas.countries import CountryResponseSchema
from src.schemas.genres import GenreResponseSchema
from src.schemas.languages import LanguageResponseSchema


class MovieDetailSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        one_year = datetime.date.today() + datetime.timedelta(days=365)
        if value > one_year:
            raise ValueError("Date must be less than 1 year from now")
        return value

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }


class MovieResponseSchema(MovieDetailSchema):
    id: int
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    model_config = {
        "from_attributes": True,
    }


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {
        "from_attributes": True
    }


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MoviePatchSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: float) -> float:
        if value is None:
            return value
        if not 0 <= value <= 100:
            raise ValueError("score must be within range 0 - 100")
        return value

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, value: float) -> float:
        if value is None:
            return value
        if value < 0:
            raise ValueError("budget must be more than 0")
        return value

    @field_validator("revenue")
    @classmethod
    def validate_revenue(cls, value: float) -> float:
        if value is None:
            return value
        if value < 0:
            raise ValueError("revenue must be more than 0")
        return value

    model_config = {
        "arbitrary_types_allowed": True
    }
