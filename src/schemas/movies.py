from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, Field

from src.database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class CountrySchema(BaseModel):
    id: int
    name: Optional[str] = None
    code: str

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


class MovieReadSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    country: CountrySchema

    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    genre_ids: list[int]
    actor_ids: list[int]
    language_ids: list[int]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("genre_ids", mode="before")
    @classmethod
    def extract_genre_ids(cls, v):
        if isinstance(v, list):
            return [item.id for item in v] if v and hasattr(v[0], "id") else v
        return v or []

    @field_validator("actor_ids", mode="before")
    @classmethod
    def extract_actor_ids(cls, v):
        if isinstance(v, list):
            return [item.id for item in v] if v and hasattr(v[0], "id") else v
        return v or []

    @field_validator("language_ids", mode="before")
    @classmethod
    def extract_language_ids(cls, v):
        if isinstance(v, list):
            return [item.id for item in v] if v and hasattr(v[0], "id") else v
        return v or []


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return value


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
    country: Optional[str] = None
    genres: Optional[list[str]] = None
    actors: Optional[list[str]] = None
    languages: Optional[list[str]] = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return value

        if value > date.today() + timedelta(days=365):
            raise ValueError(
                "Date cannot be more than one year in the future."
            )

        return value
