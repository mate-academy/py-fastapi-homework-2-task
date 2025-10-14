from __future__ import annotations

from typing import List, Optional
from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, Field, validator


class CountryOut(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class SimpleIdName(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(...)
    overview: str = Field(..., min_length=1)
    status: str = Field(...)
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=1, max_length=3)
    genres: List[str] = Field(default_factory=list)
    actors: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    @validator("date")
    def date_not_too_far(cls, v: date) -> date:
        if v > (date.today() + timedelta(days=365)):
            raise ValueError("date must not be more than one year in the future")
        return v

    @validator("score")
    def score_range(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("score must be between 0 and 100")
        return v


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @validator("date")
    def date_not_too_far(cls, v: date) -> date:
        if v is not None and v > (date.today() + timedelta(days=365)):
            raise ValueError("date must not be more than one year in the future")
        return v

    @validator("score")
    def score_range(cls, v: float) -> float:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("score must be between 0 and 100")
        return v


class MoviesListResponse(BaseModel):
    movies: List[MovieShortOut]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieOut(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[CountryOut]
    genres: Optional[List[SimpleIdName]]
    actors: Optional[List[SimpleIdName]]
    languages: Optional[List[SimpleIdName]]

    # model_config = ConfigDict(from_attributes=True, extra="ignore", populate_by_name=True, exclude_none=True)
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
        exclude_none=True,  # ← ключевой параметр
    )
  
  
class MovieShortOut(BaseModel):
    id: int
    name: str
    date: date
    overview: str
    score: float

    class Config:
        from_attributes = True


# --- Aliases for test compatibility ---
MovieListItemSchema = MovieOut
MovieDetailSchema = MovieOut
MovieCreateSchema = MovieCreate
MovieUpdateSchema = MovieUpdate
MovieListResponseSchema = MoviesListResponse
