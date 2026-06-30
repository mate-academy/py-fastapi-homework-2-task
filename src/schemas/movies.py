from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


def _validate_movie_date_logic(v):
    # if v is None:
    #     return v
    # if isinstance(v, str):
    #     from datetime import datetime
    #     try:
    #         v = datetime.strptime(v, "%Y-%m-%d").date()
    #     except ValueError:
    #         return v
    # max_date = date.today().replace(year=date.today().year + 10)
    # if v > max_date:
    #     raise ValueError("Date cannot be more than one year in the future.")
    if v is None:
        return v

    if isinstance(v, str):
        try:
            v = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            return v
    elif isinstance(v, datetime):
        v = v.date()

    max_date = date.today() + relativedelta(years=1)
    if v > max_date:
        raise ValueError("Date cannot be more than one year in the future.")

    return v


class CountryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: Optional[str] = None


class GenreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MovieListElement(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: str


class PaginatedMoviesResponse(BaseModel):
    movies: List[MovieListElement]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"] = Field(..., description="Status of the movie")
    budget: Decimal = Field(..., ge=0)
    revenue: Decimal = Field(..., ge=0)
    country: str = Field(..., min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_not_too_future(cls, v):
        return _validate_movie_date_logic(v)


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: date
    score: float
    overview: Optional[str] = None
    status: str
    budget: float
    revenue: float
    country: Optional[CountryResponse] = None
    genres: List[GenreResponse] = []
    actors: List[ActorResponse] = []
    languages: List[LanguageResponse] = []


class MovieUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[Literal["Released", "Post Production", "In Production"]] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    revenue: Optional[Decimal] = Field(None, ge=0)

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_not_too_future(cls, v):
        return _validate_movie_date_logic(v)


MovieListResponseSchema = PaginatedMoviesResponse
MovieDetailedResponse = MovieDetailSchema
MovieListItemSchema = MovieListElement
