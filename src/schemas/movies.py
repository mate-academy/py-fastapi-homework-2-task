import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# -------------------------
# Nested schemas
# -------------------------

class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str] = None


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


# -------------------------
# Movie schemas (IMPORTANT NAMES)
# -------------------------

class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


# -------------------------
# Requests
# -------------------------

class MovieCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"Released", "Post Production", "In Production"}
        if value not in allowed:
            raise ValueError(f"Status must be one of {sorted(allowed)}")
        return value


class MovieUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: Optional[datetime.date]) -> Optional[datetime.date]:
        if value is None:
            return value

        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        allowed = {"Released", "Post Production", "In Production"}
        if value not in allowed:
            raise ValueError(f"Status must be one of {sorted(allowed)}")
        return value
