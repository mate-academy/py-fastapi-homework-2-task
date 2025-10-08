from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator, Field
from datetime import date, timedelta

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name:str
    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieResponseSchema(BaseModel):
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
    model_config = ConfigDict(from_attributes=True)



class MovieErrorSchema(BaseModel):
    detail: str


class MovieSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    model_config = ConfigDict(from_attributes=True)


class MovieListSchema(BaseModel):
    movies: List[MovieSchema]
    total_items: int
    total_pages: int
    prev_page: Optional[str] = None
    next_page: Optional[str] = None

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
    country: Optional[CountrySchema]
    genres: List[GenreSchema] = []
    actors: List[ActorSchema] = []
    languages: List[LanguageSchema] = []
    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str] = []
    actors: List[str] = []
    languages: List[str] = []
    model_config = ConfigDict(from_attributes=True)

    @field_validator("date")
    def validate_date(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError(
                "The date must not be more than one year in the future.")
        return value


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(ge=0, le=100, default=None)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(ge=0, default=None)
    revenue: Optional[float] = Field(ge=0, default=None)
