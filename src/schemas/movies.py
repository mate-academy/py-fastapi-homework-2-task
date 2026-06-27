import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, Field


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
    date: datetime.date
    score: float
    overview: str
    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieListItemSchema):
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str = Field(min_length=1)
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: datetime.date) -> datetime.date:
        if v > datetime.date.today():
            raise ValueError("Date must not be in the future.")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = Field(default=None, min_length=1)
    status: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: Optional[datetime.date]) -> Optional[datetime.date]:
        if v and v > datetime.date.today():
            raise ValueError("Date must not be in the future.")
        return v


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    total_items: int
    total_pages: int
    prev_page: Optional[str]
    next_page: Optional[str]
    model_config = ConfigDict(from_attributes=True)
