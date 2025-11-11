from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: Optional[date]
    score: Optional[float]
    overview: Optional[str]

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str]
    status: str
    budget: float
    revenue: float
    country: Optional[dict]
    genres: List[dict]
    actors: List[dict]
    languages: List[dict]


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: Optional[str] = None
    status: str
    budget: float = Field(..., ge=0)
    revenue: Optional[float] = Field(0, ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    def validate_date(cls, v: date):
        if v > date.today() + timedelta(days=365):
            raise ValueError(
                "Date cannot be more than one year in the future.")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    def validate_date(cls, value: Optional[date]):
        if value and value > date.today() + timedelta(days=365):
            raise ValueError(
                "Date cannot be more than one year in the future.")
        return value
