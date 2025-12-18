from typing import List, Optional
import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MovieBase(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    movies: List[MovieBase]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CountryBase(BaseModel):
    id: int
    code: str
    name: Optional[str] | None = None

    model_config = ConfigDict(from_attributes=True)


class GenresBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorsBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguagesBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, movie_date: datetime.date):
        year_later = datetime.date.today().replace(
            year=datetime.date.today().year + 1
        )
        if movie_date > year_later:
            raise ValueError("Date cannot be more than one year in the future")
        return movie_date


class MovieDetailResponse(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryBase
    genres: List[GenresBase]
    actors: List[ActorsBase]
    languages: List[LanguagesBase]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
