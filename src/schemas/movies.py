from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str  # ISO 3166-1 alpha-3
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    def validate_date(cls, value):
        if value > date.today() + timedelta(days=365):
            raise ValueError("Invalid input data.")
        return value

    @field_validator("status")
    def validate_status(cls, value):
        allowed = {"Released", "Post Production", "In Production"}
        if value not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return value


class SimpleEntity(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CountryOut(BaseModel):
    id: int
    code: str
    name: str | None

    class Config:
        from_attributes = True


class MovieCreatedResponse(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryOut
    genres: List[SimpleEntity]
    actors: List[SimpleEntity]
    languages: List[SimpleEntity]

    class Config:
        from_attributes = True


class MovieOut(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListItemSchema(MovieOut):
    pass


class MovieListResponseSchema(BaseModel):
    movies: List[MovieOut]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    overview: Optional[str] = None
    status: Optional[str] = None
