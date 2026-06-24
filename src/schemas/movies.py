from datetime import date, timedelta
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


# --- Base Entity Schemas ---

class EntityBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Task 1: List Endpoint Schemas ---

class MovieShort(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    movies: List[MovieShort]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


# --- Task 2: Create Endpoint Schemas ---

class MovieCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(
        ...,
        min_length=2,
        max_length=3,
        pattern="^[A-Z]{2,3}$",
        description="2 or 3-letter uppercase ISO country code"
    )
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    def validate_date(cls, v):
        if v > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return v


# --- Task 3: Details Endpoint Schemas ---

class MovieDetailResponse(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Optional[CountrySchema]
    genres: List[EntityBase]
    actors: List[EntityBase]
    languages: List[EntityBase]

    model_config = ConfigDict(from_attributes=True)


# --- Task 5: Update Endpoint Schemas ---

class MovieUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[Literal["Released", "Post Production", "In Production"]] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
