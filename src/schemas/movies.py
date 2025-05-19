from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum, CountryModel


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        from_attributes = True


class GenreListSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorListSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageListSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieBaseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieBaseSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: Optional[int]
    total_items: Optional[int]

    class Config:
        from_attributes = True


class MovieDetailSchema(MovieBaseSchema):
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreListSchema]
    actors: List[ActorListSchema]
    languages: List[LanguageListSchema]

    class Config:
        from_attributes = True


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    def validate_date(cls, value: datetime.date) -> datetime.date:
        current_year = datetime.now().year
        if value.year > current_year + 1:
            raise ValueError(f"Year cannot be greater than {current_year + 1}")
        return value

    class Config:
        from_attributes = True


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: MovieStatusEnum = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    class Config:
        from_attributes = True
