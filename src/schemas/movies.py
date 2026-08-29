import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class MovieStatus(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class RelatedEntityResponseSchema(BaseModel):
    id: int  # noqa: VNE003
    name: str

    model_config = {"from_attributes": True}


class CountryResponseSchema(BaseModel):
    id: int  # noqa: VNE003
    code: str
    name: Optional[str]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int  # noqa: VNE003
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieDetailResponseSchema(MovieListItemSchema):
    status: str
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[RelatedEntityResponseSchema]
    actors: List[RelatedEntityResponseSchema]
    languages: List[RelatedEntityResponseSchema]

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateResponseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatus
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(
        min_length=2,
        max_length=3,
        pattern=r"^[A-Z]{2,3}$",
    )
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far_in_future(
        cls,
        value: datetime.date,
    ) -> datetime.date:
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError("Date must not be more than one year in the future.")
        return value


class MovieUpdateResponseSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatus] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far_in_future(
        cls,
        value: Optional[datetime.date],
    ) -> Optional[datetime.date]:
        if value is None:
            return value
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError("Date must not be more than one year in the future.")
        return value


class MovieUpdateSuccessResponseSchema(BaseModel):
    detail: str
