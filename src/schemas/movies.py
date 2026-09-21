from datetime import date as dt_date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: dt_date
    score: Optional[float] = None
    overview: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: dt_date
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[CountrySchema] = None
    genres: List[GenreSchema] = []
    actors: List[ActorSchema] = []
    languages: List[LanguageSchema] = []

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: dt_date
    score: float = Field(..., ge=0.0, le=100.0)
    overview: Optional[str] = None
    status: str
    budget: float = Field(..., ge=0.0)
    revenue: float = Field(..., ge=0.0)
    country: Optional[str] = None
    genres: List[str] = []
    actors: List[str] = []
    languages: List[str] = []

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: dt_date) -> dt_date:
        if v > dt_date.today() + timedelta(days=366):
            raise ValueError("Date cannot be more than one year in the future.")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[dt_date] = None
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0.0)
    revenue: Optional[float] = Field(None, ge=0.0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[dt_date]) -> Optional[dt_date]:
        if v is not None and v > dt_date.today() + timedelta(days=366):
            raise ValueError("Date cannot be more than one year in the future.")
        return v


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: dt_date
    score: float
    overview: Optional[str] = None
    status: str
    budget: float
    revenue: float
    country: Optional[str] = None
    genres: List[str] = []
    actors: List[str] = []
    languages: List[str] = []

    model_config = ConfigDict(from_attributes=True)
