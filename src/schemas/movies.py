from datetime import date, timedelta, datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field, field_validator, constr

from database.models import MovieStatusEnum


class GenreModel(BaseModel):
    name: str
    movies: list["MovieDetailSchema"]


class GenreDetail(GenreModel):
    id: int

    class Config:
        from_attributes = True


class GenreDetailResponse(BaseModel):
    id: int
    name: str


class ActorModel(BaseModel):
    name: str
    movies: list["MovieDetailSchema"]


class ActorDetail(ActorModel):
    id: int

    class Config:
        from_attributes = True


class ActorDetailResponse(BaseModel):
    id: int
    name: str


class CountryModel(BaseModel):
    code: str
    name: Optional[str] = None
    movies: list["MovieDetailSchema"]


class CountryDetail(CountryModel):
    id: int

    class Config:
        from_attributes = True


class CountryDetailResponse(BaseModel):
    id: int
    code: str
    name: Optional[str] = None


class LanguageModel(BaseModel):
    name: str
    movies: list["MovieDetailSchema"]


class LanguageDetail(LanguageModel):
    id: int

    class Config:
        from_attributes = True


class LanguageDetailResponse(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    name: str
    date: date
    score: float = Field(ge=0, le=100, description="Score value must be between 0 and 100")
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0, description="Budget must be greater than or equal to 0")
    revenue: float = Field(ge=0, description="Revenue must be greater than or equal to 0")
    country_id: int
    country: CountryDetail
    genres: list["GenreDetail"]
    actors: list["ActorDetail"]
    languages: list["LanguageDetail"]


class MoviePutRequest(BaseModel):
    name: constr(max_length=255)
    date: date
    score: float = Field(ge=0, le=100, description="Score value must be between 0 and 100")
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0, description="Budget must be greater than or equal to 0")
    revenue: float = Field(ge=0, description="Revenue must be greater than or equal to 0")
    country: str = Field(pattern=r"^[A-Z]{2}$", description="Must be a valid ISO 3166-1 alpha-2 country code")
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date", mode="before")
    @classmethod
    def date_not_too_far_in_future(cls, value: date) -> date:
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d").date()
        max_allowed_date = date.today() + timedelta(days=365)
        if value > max_allowed_date:
            raise ValueError("Date must not be more than one year in the future.")
        return value


class MoviePostResponseSchema(BaseModel):
    name: str
    date: str
    score: float = Field(ge=0, le=100, description="Score value must be between 0 and 100")
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0, description="Budget must be greater than or equal to 0")
    revenue: float = Field(ge=0, description="Revenue must be greater than or equal to 0")
    country_id: int
    country: CountryDetailResponse
    genres: list["GenreDetailResponse"]
    actors: list["ActorDetailResponse"]
    languages: list["LanguageDetailResponse"]


class MovieDetailResponseSchema(MoviePostResponseSchema):
    id: int

    class Config:
        from_attributes = True


class MovieDetailSchema(MovieBase):
    id: int

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: str
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MoviePatchResponseSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Score value must be between 0 and 100"
    )
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="Budget must be greater than or equal to 0"
    )
    revenue: Optional[float] = Field(
        default=None,
        ge=0,
        description="Revenue must be greater than or equal to 0"
    )
