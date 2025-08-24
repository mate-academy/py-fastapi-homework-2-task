from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, ConfigDict, field_validator, validator, constr
from typing import List, Optional, Literal


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    def validate_date(self, v: datetime):
        if v > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Movie date cannot be more than 1 year in the future")
        return v


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

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


class MovieCreateDetailSchema(MovieBase):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @validator("country")
    def validate_country(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Country code must be exactly 3 alphabetic characters (ISO 3166-1 alpha-3)")
        return v.upper()


class MovieDetailSchema(MovieBase):
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateRequest(BaseModel):
    name: constr(max_length=255) | None
    date: date | None
    score: float | None
    overview: str | None
    status: Literal["Released", "Post Production", "In Production"] | None
    country: str | None
    genres: List[str] | None
    actors: List[str] | None
    languages: List[str] | None

    @validator("date")
    def date_not_too_far(cls, v: date) -> date:
        if v > date.today() + timedelta(days=365):
            raise ValueError("Release date cannot be more than one year in the future")
        return v

    @validator("country")
    def validate_country(cls, v: str) -> str:
        if v and (len(v) != 3 or not v.isalpha()):
            raise ValueError("Country code must be exactly 3 alphabetic characters (ISO 3166-1 alpha-3)")
        return v.upper()


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieItemSchema(MovieDetailSchema):
    id: int


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
