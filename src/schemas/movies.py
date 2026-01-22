from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date, timedelta
from typing import List, Optional


class MovieBaseSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float

    model_config = ConfigDict(from_attributes=True)


class MovieResponseBaseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(MovieBaseSchema):
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("name")
    @classmethod
    def name_max_length(cls, v):
        if len(v) > 255:
            raise ValueError("Name must not exceed 255 characters.")
        return v

    @field_validator('date')
    @classmethod
    def date_not_too_far(cls, v):
        if v > date.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return v

    @field_validator('score')
    @classmethod
    def score_range(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100.")
        return v

    @field_validator("status")
    @classmethod
    def status_check(cls, v):
        allowed = {"Released", "Post Production", "In Production"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

    @field_validator("budget", "revenue")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("Value must be non-negative.")
        return v


class MovieDetailResponseSchema(MovieResponseBaseSchema):
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Invalid input data.")
        return v

    @field_validator("budget", "revenue")
    @classmethod
    def validate_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("Invalid input data.")
        return v


MovieDetailSchema = MovieDetailResponseSchema
