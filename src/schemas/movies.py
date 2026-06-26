from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CountryBase(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GenreBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
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
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date_future(cls, v):
        max_future = date(datetime.now().year + 1, datetime.now().month, datetime.now().day)
        if v > max_future:
            raise ValueError("Date cannot be more than one year in the future.")
        return v


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryBase
    genres: list[GenreBase]
    actors: list[ActorBase]
    languages: list[LanguageBase]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: Optional[date] = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: str | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date_future(cls, v):
        if v is not None:
            max_future = date(datetime.now().year + 1, datetime.now().month, datetime.now().day)
            if v > max_future:
                raise ValueError("Date cannot be more than one year in the future.")
        return v


MovieDetailResponseSchema = MovieDetailSchema
MovieCreateRequestSchema = MovieCreateSchema
MovieUpdateRequestSchema = MovieUpdateSchema
