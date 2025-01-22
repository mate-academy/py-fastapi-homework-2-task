import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MovieSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponse(BaseModel):
    movies: list[MovieSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}


class MovieCreateRequest(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(gt=0, le=100)
    overview: str
    status: str
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = {"from_attributes": True}


class GenreResponse(BaseModel):
    id: int
    name: str


class ActorResponse(BaseModel):
    id: int
    name: str


class LanguageResponse(BaseModel):
    id: int
    name: str


class CountryResponse(BaseModel):
    id: int
    code: str
    name: Optional[str]


class MovieCreateResponse(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponse
    genres: list[GenreResponse]
    actors: list[ActorResponse]
    languages: list[LanguageResponse]

    model_config = {"from_attributes": True}


class MovieDetailResponse(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponse
    genres: list[GenreResponse]
    actors: list[ActorResponse]
    languages: list[LanguageResponse]

    model_config = {"from_attributes": True}


class MovieUpdateRequest(BaseModel):
    name: str | None = None
    date: str | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: str | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    model_config = {"from_attributes": True}
