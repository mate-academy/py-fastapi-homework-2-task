import datetime

from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

from schemas.actors import ActorResponseSchema
from schemas.countries import CountryResponseSchema
from schemas.genres import GenreResponseSchema
from schemas.languages import LanguagesResponseSchema


class MovieBase(BaseModel):
    id: int
    name: str | None


class MovieResponseSchema(MovieBase):
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieResponseSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str] = []
    actors: List[str] = []
    languages: List[str] = []

    model_config = {"from_attributes": True}

    @field_validator("date")
    def validate_date(cls, date):
        if date > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must be less than 1 year from today.")
        return date


class MovieDetailSchema(MovieBase):
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguagesResponseSchema]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    pass


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: Literal["Released", "Post Production", "In Production"] | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
