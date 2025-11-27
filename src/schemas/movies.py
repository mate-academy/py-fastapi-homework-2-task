import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, v: datetime.date) -> datetime.date:
        max_future_date = datetime.date.today() + datetime.timedelta(days=365)
        if v > max_future_date:
            raise ValueError("Release date cannot be more than one year in the future.")
        return v

    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)


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


class MovieDetailSchema(MovieBase):
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieCreateResponseSchema(MovieDetailSchema):
    id: int


class MovieUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, v: datetime.date | None) -> datetime.date | None:
        if v is None:
            return v
        max_future_date = datetime.date.today() + datetime.timedelta(days=365)
        if v > max_future_date:
            raise ValueError("Release date cannot be more than one year in the future.")
        return v

    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


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
