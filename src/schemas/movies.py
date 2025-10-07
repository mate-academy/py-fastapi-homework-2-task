from __future__ import annotations

import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

_ALLOWED_STATUSES = {"Released", "Post Production", "In Production"}


class NamedEntity(BaseModel):
    id: int
    name: str


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None


class MovieBriefSchema(BaseModel):
    id: int
    name: str
    date: dt.date
    score: float
    overview: str


class MovieFullSchema(BaseModel):
    id: int
    name: str
    date: dt.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Optional[CountrySchema] = None
    genres: List[NamedEntity] = Field(default_factory=list)
    actors: List[NamedEntity] = Field(default_factory=list)
    languages: List[NamedEntity] = Field(default_factory=list)


class MoviesListResponse(BaseModel):
    movies: List[MovieBriefSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: dt.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str] = Field(default_factory=list)
    actors: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: dt.date) -> dt.date:
        if v > (dt.date.today() + dt.timedelta(days=365)):
            raise ValueError("date must not be more than one year in the future")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in _ALLOWED_STATUSES:
            raise ValueError("status must be one of: Released | Post Production | In Production")
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        # Якщо потрібно строго alpha-3: заміни умову на: len(v) == 3
        if not (v.isalpha() and v.isupper() and len(v) in (2, 3)):
            raise ValueError("country must be an uppercase ISO code (2–3 letters)")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[dt.date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[dt.date]) -> Optional[dt.date]:
        if v is None:
            return v
        if v > (dt.date.today() + dt.timedelta(days=365)):
            raise ValueError("date must not be more than one year in the future")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in _ALLOWED_STATUSES:
            raise ValueError("status must be one of: Released | Post Production | In Production")
        return v
