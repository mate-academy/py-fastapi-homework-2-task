from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import List, Optional
from datetime import date


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("date")
    @staticmethod
    def serialize_date(value: date) -> str:
        return value.isoformat()


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("date")
    @staticmethod
    def serialize_date(value: date) -> str:
        return value.isoformat()


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date]
    score: Optional[float]
    overview: Optional[str]
    status: Optional[str]
    budget: Optional[float]
    revenue: Optional[float]
