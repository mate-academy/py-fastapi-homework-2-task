from datetime import date, timedelta
from typing import List, Optional

from pydantic import BaseModel, confloat, field_validator, Field
from pydantic_extra_types.country import CountryAlpha3
from database.models import MovieStatusEnum


class CountryListSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]
    model_config = {"from_attributes": True}


class GenreListSchema(BaseModel):
    id: int
    name: str


class ActorListSchema(BaseModel):
    id: int
    name: str


class LanguageListSchema(BaseModel):
    id: int
    name: str


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    movies: List[MovieDetailSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    class Config:
        from_attributes = True


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: confloat(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: confloat(ge=0)
    revenue: confloat(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True

    @classmethod
    @field_validator("country")
    def country_validator(cls, value: str) -> str:
        if not value.isalpha() or not value.isupper():
            raise ValueError("Country code should be in uppercase")
        return value

    @classmethod
    @field_validator("date")
    def date_validator(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError(
                "The date must not be more than one year in the future"
            )
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
    genres: List[GenreListSchema]
    actors: List[ActorListSchema]
    languages: List[LanguageListSchema]

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
