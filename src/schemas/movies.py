from pydantic import BaseModel, ConfigDict, field_validator
import datetime
from typing import Optional
from src.database.models import MovieStatusEnum


class ActorSchema(BaseModel):
    id: int
    name: Optional[str] = None
    model_config: ConfigDict = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: Optional[str] = None
    model_config: ConfigDict = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: Optional[str] = None
    model_config: ConfigDict = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: Optional[str] = None
    name: Optional[str] = None

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Optional[str] = ""
    genres: Optional[list[str]] = []
    actors: Optional[list[str]] = []
    languages: Optional[list[str]] = []

    model_config: ConfigDict = ConfigDict(from_attributes=True)

    @field_validator("score")
    def validate_score(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100.")
        return v

    @field_validator("budget", "revenue")
    def validate_non_negative(cls, v: float, info) -> float:
        if v < 0:
            raise ValueError(f"{info.field_name.capitalize()} must be non-negative.")
        return v

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if len(v) > 255:
            raise ValueError("Name must not exceed 255 characters.")
        return v

    @field_validator("date")
    def validate_date(cls, v: datetime.date) -> datetime.date:
        if v > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    model_config: ConfigDict = ConfigDict(from_attributes=True)

    @field_validator("score")
    def validate_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100.")
        return v

    @field_validator("budget", "revenue")
    def validate_non_negative(cls, v: Optional[float], info) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"{info.field_name.capitalize()} must be non-negative.")
        return v

    @field_validator("name")
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 255:
            raise ValueError("Name must not exceed 255 characters.")
        return v

    @field_validator("date")
    def validate_date(cls, v: Optional[datetime.date]) -> Optional[datetime.date]:
        if v is not None and v > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return v


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    actors: Optional[list[ActorSchema]] = []
    genres: Optional[list[GenreSchema]] = []
    languages: Optional[list[LanguageSchema]] = []
    country: Optional[CountrySchema] = None


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config: ConfigDict = ConfigDict(from_attributes=True)
