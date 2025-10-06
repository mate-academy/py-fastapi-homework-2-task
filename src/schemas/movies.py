from datetime import date, timedelta
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class MovieBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str

    @field_validator("date")
    def validate_date(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieListItemSchema(MovieBaseSchema):
    id: int


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieErrorSchema(BaseModel):
    detail: str


class MovieBaseCreateSchema(MovieBaseSchema):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)


class MovieCreateRequestSchema(MovieBaseCreateSchema):
    country: str = Field(max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]


class CountryBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str = Field(max_length=3)
    name: Optional[str] = None


class GenreBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieCreateResponseSchema(MovieBaseCreateSchema):
    country: CountryBaseSchema
    genres: List[GenreBaseSchema]
    actors: List[ActorBaseSchema]
    languages: List[LanguageBaseSchema]
    id: int


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @field_validator("date")
    def validate_date(cls, value: Optional[date]) -> date:
        if value is not None and value > date.today() + timedelta(days=365):
            raise ValueError("Invalid input data.")
        return value

    @field_validator("score")
    def validate_score(cls, value: Optional[float]) -> date:
        if value is not None and (value < 0 or value > 100):
            raise ValueError("Invalid input data.")
        return value

    @field_validator("budget", "revenue")
    def validate_budget(cls, value: Optional[float]) -> date:
        if value is not None and value < 0:
            raise ValueError("Invalid input data.")
        return value


class MovieUpdateResponseShema(BaseModel):
    detail: str
