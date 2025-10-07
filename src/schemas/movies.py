from datetime import date, timedelta
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class GenreBaseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorBaseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountryBaseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class LanguageBaseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieErrorSchema(BaseModel):
    detail: str


class MovieShortSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListSchema(BaseModel):
    movies: List[MovieShortSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieShortSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryBaseSchema
    genres: List[GenreBaseSchema]
    actors: List[ActorBaseSchema]
    languages: List[LanguageBaseSchema]


class MovieCreateBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    def validate_date(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieCreateRequestSchema(MovieCreateBaseSchema):
    country: str = Field(max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieCreateResponseSchema(MovieCreateBaseSchema):
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

    @field_validator("score")
    def validate_score(cls, value: Optional[float]) -> float:
        if value is not None and not (0 <= value <= 100):
            raise ValueError("Invalid input data.")
        return value

    @field_validator("date")
    def validate_date(cls, value: date) -> date:
        if value is not None and value > date.today() + timedelta(days=365):
            raise ValueError("Invalid input data.")
        return value

    @field_validator("budget", "revenue")
    def validate_budget(cls, value: Optional[float]) -> float:
        if value is not None and value < 0:
            raise ValueError("Invalid input data.")
        return value


class MovieUpdateResponseShema(BaseModel):
    detail: str
