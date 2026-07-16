import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ActorBaseSchema(BaseModel):
    name: str = Field(max_length=255)


class ActorSchema(ActorBaseSchema):
    id: int

    model_config = {
        "from_attributes": True
    }


class GenreBaseSchema(BaseModel):
    name: str = Field(max_length=255)


class GenreSchema(GenreBaseSchema):
    id: int

    model_config = {
        "from_attributes": True
    }


class CountryBaseSchema(BaseModel):
    code: str = Field(max_length=3)
    name: Optional[str] = Field(max_length=255)


class CountrySchema(CountryBaseSchema):
    id: int

    model_config = {
        "from_attributes": True
    }


class LanguageBaseSchema(BaseModel):
    name: str = Field(max_length=255)


class LanguageSchema(LanguageBaseSchema):
    id: int

    model_config = {
        "from_attributes": True
    }


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str = Field(max_length=50)
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieListResponseSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str

    model_config = {
        "from_attributes": True
    }


class MovieDetailResponseSchema(MovieBaseSchema):
    id: int

    model_config = {
        "from_attributes": True
    }


class PaginatedMovieListResponseSchema(BaseModel):
    movies: List[MovieListResponseSchema]
    prev_page: Optional[str] = ""
    next_page: Optional[str] = ""
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_future_date(cls, v: datetime.date) -> datetime.date:
        today = datetime.date.today()
        one_year_later = today.replace(year=today.year + 1)
        if v > one_year_later:
            raise ValueError("Movie date must not be more than one year in the future.")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(ge=0, le=100, default=None)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(ge=0, default=None)
    revenue: Optional[float] = Field(ge=0, default=None)
    country: Optional[str] = Field(max_length=3, default=None)
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    @field_validator("date")
    @classmethod
    def validate_future_date(cls, v: datetime.date) -> datetime.date:
        today = datetime.date.today()
        one_year_later = today.replace(year=today.year + 1)
        if v > one_year_later:
            raise ValueError("Movie date must not be more than one year in the future.")
        return v
