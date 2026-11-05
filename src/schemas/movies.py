from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ItemSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieItem(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: date):
        if value > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than 1 year in the future.")
        return value

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieItem):
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[ItemSchema] = Field(default_factory=list)
    actors: list[ItemSchema] = Field(default_factory=list)
    languages: list[ItemSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieItem]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: date):
        if value > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than 1 year in the future.")
        return value


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: Optional[date]):
        if value is not None and value > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than 1 year in the future.")
        return value
