# Write your code here
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=50)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class MovieBase(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True


class MoviesListResponseSchema(BaseModel):
    movies: List[MovieBase]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        arbitrary_types_allowed = True

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        current_year = datetime.now().year
        if value.year > current_year + 1:
            raise ValueError(f"The year in 'date' cannot be greater than {current_year + 1}.")
        return value


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
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        from_attributes = True


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True
