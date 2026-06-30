import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str] = None


class RelatedEntitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: datetime.date) -> datetime.date:
        max_allowed_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_allowed_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value


class MovieCreateSchema(MovieBaseSchema):
    country: str = Field(min_length=1, max_length=3)
    genres: list[str] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: Optional[datetime.date]) -> Optional[datetime.date]:
        if value is None:
            return value

        max_allowed_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_allowed_date:
            raise ValueError("Date cannot be more than one year in the future.")
        return value


class MovieDetailSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: CountrySchema
    genres: list[RelatedEntitySchema]
    actors: list[RelatedEntitySchema]
    languages: list[RelatedEntitySchema]


class DetailMessageSchema(BaseModel):
    detail: str
