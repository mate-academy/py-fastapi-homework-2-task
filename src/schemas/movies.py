from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MovieStatus(str, Enum):
    """Enum для статуса фильма"""
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class CountrySchema(BaseModel):
    """Схема для страны"""
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class GenreSchema(BaseModel):
    """Схема для жанра"""
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    """Схема для актера"""
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageSchema(BaseModel):
    """Схема для языка"""
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    """Схема для элемента списка фильмов"""
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    """Схема для ответа со списком фильмов"""
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    """Схема для детальной информации о фильме"""
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        from_attributes = True


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=3, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator('date')
    @classmethod
    def validate_date(cls, v: date) -> date:
        max_future_date = date.today() + timedelta(days=365)
        if v > max_future_date:
            raise ValueError('Date must not be more than one year in the future')
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


class MovieUpdateResponseSchema(BaseModel):
    detail: str