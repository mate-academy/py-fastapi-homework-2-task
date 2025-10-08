from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, timedelta

from database.models import MovieStatusEnum


class MovielistSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovielistSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorsSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorsSchema]
    languages: List[LanguageSchema]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str = Field(max_length=255)
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        if value is None:
            return value
        value = value.upper()
        if len(value) > 3:
            raise ValueError("country must be up to 3-letter ISO alpha-3 code")
        return value

    @field_validator("genres", "actors", "languages", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: List[str]) -> List[str]:
        return [item.title() for item in value]

    @field_validator("date")
    @classmethod
    def date_validation(cls, value: date) -> date:
        today = date.today()
        max_date = today + timedelta(days=365)
        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
