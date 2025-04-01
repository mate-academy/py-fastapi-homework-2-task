from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime, timedelta
from database.models import MovieStatusEnum
from typing import Optional


class GenreListSchema(BaseModel):
    id: int
    name: str


class ActorListSchema(BaseModel):
    id: int
    name: str


class CountryListSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class LanguageListSchema(BaseModel):
    id: int
    name: str


class MovieListResponseSchema(BaseModel):
    id: int
    name: str
    date: date


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: Optional[date] = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    movies: list[MovieDetailSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    class Config:
        from_attributes = True

    @classmethod
    @field_validator("date")
    def validate_date(cls, value):
        max_allowed_date = datetime.utcnow().date() + timedelta(days=365)
        if value > max_allowed_date:
            raise ValueError("Date must not be more than one year in the future.")
        return value

    @classmethod
    @field_validator("country")
    def country_code_validate(cls, value):
        if len(value) != 3:
            raise ValueError("Country should be defined according to ISO 3166-1 alpha-3 code")
        if not value.isupper():
            raise TypeError("Country code should be uppercase")
        return value


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryListSchema
    genres: list[GenreListSchema]
    actors: list[ActorListSchema]
    languages: list[LanguageListSchema]

    class Config:
        from_attributes = True
