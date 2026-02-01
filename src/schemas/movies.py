from pydantic import BaseModel, Field, field_validator
from datetime import date, timedelta

from database.models import MovieStatusEnum


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None

    class Config:
        from_attributes = True


class NamedEntityResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieResponseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str | None = Field(None, min_length=2, max_length=5)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def date_not_too_far(cls, v: date) -> date:
        max_date = date.today() + timedelta(days=365)
        if v > max_date:
            raise ValueError(
                "Movie date cannot be more than 1 year in the future"
            )
        return v


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    date: date | None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None
    status: MovieStatusEnum | None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
    country: str | None
    genres: list[str] | None
    actors: list[str] | None
    languages: list[str] | None

    @field_validator("date")
    @classmethod
    def date_not_too_far(cls, v: date | None) -> date | None:
        if v is None:
            return v
        today = date.today()
        max_date = today + timedelta(days=365)
        if v > max_date:
            raise ValueError(
                "Movie date cannot be more than 1 year in the future"
            )
        return v


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[NamedEntityResponseSchema]
    actors: list[NamedEntityResponseSchema]
    languages: list[NamedEntityResponseSchema]

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float

    class Config:
        from_attributes = True
