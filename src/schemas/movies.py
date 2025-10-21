from datetime import date, timedelta
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class CountryOut(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = {"from_attributes": True}


class NamedOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str] = None

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: Optional[str] = None
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: Optional[str] = Field(None, min_length=2, max_length=3)
    genres: List[str] = []
    actors: List[str] = []
    languages: List[str] = []

    @field_validator("date")
    @classmethod
    def not_too_far_in_future(cls, v: date) -> date:
        if v > date.today() + timedelta(days=366):
            raise ValueError("date must not be more than one year in the future")
        return v


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str] = None
    status: str
    budget: float
    revenue: float
    country: Optional[CountryOut] = None
    genres: List[NamedOut] = []
    actors: List[NamedOut] = []
    languages: List[NamedOut] = []

    model_config = {"from_attributes": True}


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[Literal["Released", "Post Production", "In Production"]] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
