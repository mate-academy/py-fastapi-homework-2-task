from enum import Enum
from re import match

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date


class MovieStatusEnum(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"

    @field_validator("status")
    def validate_status_acceptable(cls, v):
        if v not in ["Released", "Post Production", "In Production"]:
            raise ValueError("status must be one of (Released | Post Production | In Production)")
        return v


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    # validator for checking format ISO 3166-1 alpha-2
    @field_validator("code")
    def validate_code_iso_3166_1(cls, v):
        if not match(r"^[A-Z]{2}$", v):
            raise ValueError("code must be a valid ISO 3166-1 alpha-2 code")
        return v


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
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    class Config:
        from_attributes = True

    @field_validator("name")
    def validate_name_length(cls, v):
        if len(v) > 255:
            raise ValueError("The name must not exceed 255 characters.")
        return v

    @field_validator("date")
    def validate_date_not_more_1_year(cls, v):
        if v > date.today() + relativedelta(years=1):
            raise ValueError("The date must not be more than one year in the future.")
        return v

    @field_validator("score")
    def validate_score_0_100(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("The score must be between 0 and 100.")
        return v

    @field_validator("budget")
    def validate_budget_positive(cls, v):
        if not v >= 0:
            raise ValueError("The budget must be non-negative.")
        return v

    @field_validator("revenue")
    def validate_revenue_positive(cls, v):
        if not v >= 0:
            raise ValueError("The revenue must be non-negative.")
        return v


class MovieListResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str


class PageSchema(BaseModel):
    items: List[MovieListResponseSchema]
    total: int
    prev_page: Optional[str] = None
    next_page: Optional[str]


class MovieAddSchema(MovieBase):
    country: str
    genres: List[str] = None
    actors: List[str] = None
    languages: List[str] = None


class MovieDetailsResponseSchema(MovieBase):
    id: int
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieUpdateSchema(MovieBase):
    name: Optional[str] = None
    date: Optional[date] = date
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    class Config:
        from_attributes = True
        exclude = {"country", "genres", "actors", "languages"}


class MovieUpdateResponseSchema(MovieDetailsResponseSchema):
    detail: str
