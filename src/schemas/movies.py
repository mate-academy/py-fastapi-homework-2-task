from datetime import date
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class StatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class CountryBase(BaseModel):
    code: str
    name: Optional[str]


class CountryResponse(CountryBase):
    id: int


class GenreBase(BaseModel):
    name: str


class GenreResponse(GenreBase):
    id: int


class ActorBase(BaseModel):
    name: str


class ActorResponse(ActorBase):
    id: int


class LanguageBase(BaseModel):
    name: str


class LanguageResponse(LanguageBase):
    id: int


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: StatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieResponse(MovieBase):
    id: int
    country: CountryResponse
    genres: List[GenreResponse]
    actors: List[ActorResponse]
    languages: List[LanguageResponse]

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
        }


class MovieDetailSchema(MovieResponse):
    pass


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[StatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    model_config = {
        "from_attributes": True,
    }
