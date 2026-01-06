import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer

from src.database.models import MovieStatusEnum


class GenreForMoviesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorForMoviesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageForMoviesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CountryForMoviesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str | None = None


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far_in_future(cls, v: datetime.date) -> datetime.date:
        today = datetime.date.today()
        max_date = today.replace(year=today.year + 1)
        if v > max_date:
            raise ValueError("date cannot be more than 1 year in the future")
        return v


class MovieDetailFields(BaseModel):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    #
    model_config = ConfigDict(arbitrary_types_allowed=True)


class MovieCreationRequestSchema(MovieBase, MovieDetailFields):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("country must be a string")
        v = v.strip().upper()
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far_in_future(cls, v: Optional[datetime.date]) -> Optional[datetime.date]:
        if v is None:
            return v
        today = datetime.date.today()
        max_date = today.replace(year=today.year + 1)
        if v > max_date:
            raise ValueError("date cannot be more than 1 year in the future")
        return v


class MovieListItemSchema(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieBase, MovieDetailFields):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: CountryForMoviesSchema
    genres: list[GenreForMoviesSchema]
    actors: list[ActorForMoviesSchema]
    languages: list[LanguageForMoviesSchema]
