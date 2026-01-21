from decimal import Decimal
from typing import Optional, List, Union
from datetime import date as DateType, timedelta

from pydantic import BaseModel, Field, field_validator, field_serializer, model_serializer, ConfigDict

from database.models import MovieStatusEnum


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
    date: Union[str, DateType]
    score: float
    overview: str

    @model_serializer
    def serialize_model(self):
        date_value = self.date
        if isinstance(date_value, DateType):
            date_value = date_value.isoformat()
        return {
            "id": self.id,
            "name": self.name,
            "date": date_value,
            "score": self.score,
            "overview": self.overview,
        }

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: Union[str, DateType]
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    country: CountrySchema
    genres: List[GenreSchema] = Field(default_factory=list)
    actors: List[ActorSchema] = Field(default_factory=list)
    languages: List[LanguageSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255, description="Movie name")
    date: DateType = Field(..., description="Release date")
    score: float = Field(..., ge=0, le=100, description="Movie score")
    overview: str = Field(..., max_length=10000, description="Movie overview")
    status: MovieStatusEnum = Field(..., description="Movie status")
    budget: float = Field(..., ge=0, description="Movie budget")
    revenue: float = Field(..., ge=0, description="Movie revenue")
    country: str = Field(
        ...,
        min_length=2,
        max_length=3,
        description="ISO 3166-1 alpha-3 country code (e.g., USA, FRA)"
    )
    genres: List[str] = Field(default_factory=list, description="List of genres")
    actors: List[str] = Field(default_factory=list, description="List of actor names")
    languages: List[str] = Field(default_factory=list, description="List of languages")

    @field_validator("date")
    @classmethod
    def validate_date_not_one_year_in_future(cls, v: DateType) -> DateType:
        max_future_date = DateType.today() + timedelta(days=365)
        if v > max_future_date:
            raise ValueError('Release date cannot be more than one year in the future')
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Movie name")
    date: Optional[DateType] = Field(None, description="Release date")
    score: Optional[float] = Field(None, ge=0, le=100, description="Movie score (0-100)")
    overview: Optional[str] = Field(None, max_length=10000, description="Movie overview")
    status: Optional[MovieStatusEnum] = Field(None, description="Movie status")
    budget: Optional[float] = Field(None, ge=0, description="Movie budget")
    revenue: Optional[float] = Field(None, ge=0, description="Movie revenue")

    @field_validator("date")
    @classmethod
    def validate_date_not_one_year_in_future(cls, v: Optional[DateType]) -> Optional[DateType]:
        if v is None:
            return v

        max_future_date = DateType.today() + timedelta(days=365)

        if v > max_future_date:
            raise ValueError("Release date cannot be more than one year in the future")
        return v


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MessageSchema(BaseModel):
    detail: str
