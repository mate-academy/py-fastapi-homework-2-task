from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

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


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float
    revenue: float
    country: Optional[CountrySchema] = None
    genres: List[GenreSchema] = []
    actors: List[ActorSchema] = []
    languages: List[LanguageSchema] = []

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    overview: Optional[str] = None
    status: Optional[str] = Field(None, max_length=15, pattern="^(Released|Post Production|In Production)$")
    budget: Optional[float] = Field(None, ge=0.0)
    revenue: Optional[float] = Field(None, ge=0.0)

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "name": "Updated Movie Name",
                "score": 95.5,
                "budget": 1500000.0
            }
        }
    )
