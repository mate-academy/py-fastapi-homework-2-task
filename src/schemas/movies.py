import datetime
from typing import Literal, List

from pydantic import BaseModel, Field, field_validator


def check_future_date(v: datetime.date | None) -> datetime.date | None:
    if v is None:
        return v
    current_year = datetime.date.today().year
    if v.year > current_year + 1:
        raise ValueError("The date must not be more than one year in the future.")
    return v


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0.0, le=100.0)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(..., ge=0.0)
    revenue: float = Field(..., ge=0.0)
    country: str = Field(..., min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_future_date(cls, v: datetime.date) -> datetime.date:
        return check_future_date(v)


class CountryResponse(BaseModel):
    id: int
    name: str | None
    code: str

    class Config:
        from_attributes = True


class NamedEntityResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponse
    genres: List[NamedEntityResponse]
    actors: List[NamedEntityResponse]
    languages: List[NamedEntityResponse]

    class Config:
        from_attributes = True


class MovieUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(None, ge=0.0, le=100.0)
    overview: str | None = None
    status: Literal["Released", "Post Production", "In Production"] | None = None
    budget: float | None = Field(None, ge=0.0)
    revenue: float | None = Field(None, ge=0.0)

    @field_validator("date")
    @classmethod
    def validate_future_date(cls, v: datetime.date | None) -> datetime.date | None:
        return check_future_date(v)


class MovieUpdateResponse(BaseModel):
    detail: str
