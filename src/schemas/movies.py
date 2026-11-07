from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_core import PydanticCustomError
from typing import List, Optional, Union
from datetime import date as DateType, datetime
from enum import Enum


# --- Base Relation Schemas for Responses ---
class GenreBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class ActorBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class CountryBase(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class LanguageBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


# --- Movie Base Schemas ---
class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    overview: Optional[str] = None
    date: DateType
    score: Optional[float] = Field(None, ge=0.0, le=100.0)

    @field_validator("date")
    @classmethod
    def validate_date_range(cls, value: DateType) -> DateType:
        current_year = datetime.now().year
        if value.year > (current_year + 1):
            raise PydanticCustomError(
                "value_error",
                "Release date cannot be more than one year into the future"
            )
        return value


class MovieStatus(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieCreate(MovieBase):
    budget: Optional[float] = Field(default=0.0, ge=0.0)
    revenue: Optional[float] = Field(default=0.0, ge=0.0)
    status: Optional[MovieStatus] = Field(default=MovieStatus.RELEASED)
    country: Optional[str] = Field(default=None)
    genres: List[str] = Field(default=[])
    actors: List[str] = Field(default=[])
    languages: List[str] = Field(default=[])


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    overview: Optional[str] = None
    date: Optional[DateType] = None
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    budget: Optional[float] = Field(None, ge=0.0)
    revenue: Optional[float] = Field(None, ge=0.0)
    status: Optional[MovieStatus] = None
    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    @field_validator("date")
    @classmethod
    def validate_date_range(cls, value: Optional[DateType]) -> Optional[DateType]:
        if value is not None:
            current_year = datetime.now().year
            if value.year > (current_year + 1):
                raise PydanticCustomError(
                    "value_error",
                    "Release date cannot be more than one year into the future"
                )
        return value


# --- Specific Route Response Structures ---

# List view item: strictly contains exactly the 5 fields tested
class MovieListItemSchema(MovieBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Full detailed item (GET by ID, POST/PATCH output)
class MovieResponse(MovieBase):
    id: int
    budget: float = 0.0
    revenue: float = 0.0
    status: str = "Released"
    genres: List[GenreBase] = []
    actors: List[ActorBase] = []
    country: Optional[CountryBase] = None
    languages: List[LanguageBase] = []
    model_config = ConfigDict(from_attributes=True)


class MoviePaginationResponse(BaseModel):
    movies: List[MovieListItemSchema]  # Enforces clean list rows
    prev_page: Optional[str] = None    # Formatted as endpoint strings
    next_page: Optional[str] = None    # Formatted as endpoint strings
    total_pages: int
    total_items: int


class MovieUpdateSuccessResponse(BaseModel):
    detail: str = "Movie updated successfully."


# --- Assignment & Test Compatibility Mapping ---
MovieDetailSchema = MovieResponse
MovieListResponseSchema = MoviePaginationResponse
MovieCreateSchema = MovieCreate
MovieUpdateSchema = MovieUpdate
