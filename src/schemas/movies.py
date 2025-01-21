import datetime
from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


class GenreResponseSchema(BaseModel):
    """Schema for genre response."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorResponseSchema(BaseModel):
    """Schema for actor response."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountryResponseSchema(BaseModel):
    """Schema for country response."""

    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class LanguageResponseSchema(BaseModel):
    """Schema for language response."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListReadResponseSchema(BaseModel):
    """Schema for movie list item response."""

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    """Schema for paginated movie list response."""

    movies: list[MovieListReadResponseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateRequestSchema(BaseModel):
    """Schema for movie creation request."""

    name: str = Field(max_length=255)
    date: datetime.date = Field(le=datetime.date.today() + timedelta(days=365))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3, description="ISO 3166-1 alpha-3 code")
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieCreateResponseSchema(BaseModel):
    """Schema for movie creation response."""

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(BaseModel):
    """Schema for detailed movie response."""

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateRequestSchema(BaseModel):
    """Schema for movie update request."""

    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = Field(None, le=datetime.date.today() + timedelta(days=365))
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
