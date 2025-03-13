import decimal
from datetime import date, datetime, timedelta
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum

Id = Annotated[int, Field(ge=1)]
Name = Annotated[str, Field(max_length=255)]
Code = Annotated[str, Field(max_length=3)]
Score = Annotated[float, Field(ge=0)]
Budget = Annotated[
    decimal.Decimal, Field(ge=0, decimal_places=2, max_digits=15)]
Revenue = Annotated[float, Field(ge=0)]


class Genre(BaseModel):
    id: Id
    name: Name

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class Actor(BaseModel):
    id: Id
    name: Name

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class Country(BaseModel):
    id: Id
    code: Code
    name: Name | None = None

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class Language(BaseModel):
    id: Id
    name: Name

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class BaseMovieSchema(BaseModel):
    name: Name
    date: date
    score: Score
    overview: str

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class MovieListItemSchema(BaseMovieSchema):
    id: Id


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseMovieSchema):
    id: Id
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Country
    genres: List[Genre]
    actors: List[Actor]
    languages: List[Language]

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class MovieCreateResponseSchema(BaseMovieSchema):
    status: MovieStatusEnum
    budget: Budget
    revenue: Revenue
    country: Code
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class MovieCreateSchema(BaseMovieSchema):
    status: MovieStatusEnum
    budget: Budget
    revenue: Revenue
    country: Code
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, date_value: date) -> date:
        max_future_date = datetime.now().date() + timedelta(days=365)
        if date_value > max_future_date:
            raise ValueError(
                "Date must not be more than one year in the future"
            )
        return date_value


class MovieUpdateSchema(BaseModel):
    name: Optional[Name] = None
    date: Optional[date] = None
    score: Optional[Score] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[Budget] = None
    revenue: Optional[Revenue] = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, score_value: Optional[float]) -> Optional[float]:
        if score_value is not None and not (0 <= score_value <= 100):
            raise ValueError("Score must be between 0 and 100")
        return score_value

    @field_validator("budget", "revenue")
    @classmethod
    def validate_non_negative(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("Budget and revenue must be non-negative")
        return value
