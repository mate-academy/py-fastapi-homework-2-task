from pydantic import BaseModel, constr, confloat, conint, Field, field_validator
from datetime import date, datetime
from typing import Optional, List, Literal

from database.models import MovieStatusEnum

class LanguageSchema(BaseModel):
    id: int
    name: str
    model_config = {
        "from_attributes": True
    }


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]
    model_config = {"from_attributes": True}


class GenreSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}

class ActorSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {
        "from_attributes": True,
    }


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = {"from_attributes": True}

class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)

    model_config = {"from_attributes": True}

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        current_year = datetime.now().year
        if value.year > current_year + 1:
            raise ValueError(
                f"The year in 'date' cannot be greater than {current_year + 1}."
            )
        return value


class MovieDetailSchema(MovieBaseSchema):
    id: int
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = {
        "from_attributes": True,
    }


class MovieUpdateSchema(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None
    date: Optional[date] = None
    score: Optional[confloat(ge=0, le=100)] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[confloat(ge=0)] = None
    revenue: Optional[confloat(ge=0)] = None
    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
    }
