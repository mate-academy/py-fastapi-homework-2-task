from datetime import date as Date, timedelta

from pydantic import BaseModel, Field, field_validator

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None = None
    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class MovieBase(BaseModel):
    name: str
    date: Date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateRequest(BaseModel):
    name: str = Field(max_length=255)
    date: Date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def date_not_too_far_in_future(cls, v):
        if v > Date.today() + timedelta(days=365):
            raise ValueError("date must not be more than one year in the future")
        return v


class MovieUpdateRequest(BaseModel):
    name: str | None = None
    date: Date | None = None
    score: float | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None


class MovieDetailSchema(MovieBase):
    id: int
    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: Date
    score: float
    overview: str
    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}
