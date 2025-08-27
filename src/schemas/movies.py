import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageModel(BaseModel):
    id: int
    name: str


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class MovieBase(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        orm_mode = True
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieBase]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CreateMovieSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=1, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        one_year = datetime.date.today() + datetime.timedelta(days=365)
        if value > one_year:
            raise ValueError(f"Date cannot be greater than {one_year}")
        return value


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageModel]

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=1, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
