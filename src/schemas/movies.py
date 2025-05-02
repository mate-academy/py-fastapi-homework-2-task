import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


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
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema] = []
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: Decimal = Field(..., ge=1)
    revenue: float = Field(..., ge=1)
    country: str = Field(..., max_length=3, min_length=2)
    genres: List[str] = Field(..., min_length=1)
    actors: List[str] = Field(..., min_length=1)
    languages: List[str] = Field(..., min_length=1)

    model_config = {"from_attributes": True}

    @field_validator("date")
    def check_future(cls, v: datetime.date):
        if v > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError(
                "Release date cannot be more than one year in the future."
            )
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[Decimal] = Field(None, ge=1)
    revenue: Optional[float] = Field(None, ge=1)

    model_config = {"from_attributes": True}
