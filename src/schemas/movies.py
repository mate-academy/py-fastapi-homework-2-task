import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, constr, field_validator

from database.models import MovieStatusEnum
from schemas.actors import ActorRetrieveSchema
from schemas.countries import CountryRetrieveSchema
from schemas.genres import GenreRetrieveSchema
from schemas.languages import LanguageRetrieveSchema


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: Optional[constr(min_length=3, max_length=3, to_upper=True)]
    genres: Optional[List[str]]
    actors: Optional[List[str]]
    languages: Optional[List[str]]

    @field_validator('date')
    def validate_date_in_future(cls, value):
        if value > datetime.date.today() + datetime.timedelta(days=364):
            raise ValueError('date cannot be more than one year in the future')
        return value


class MovieCreateSchema(MovieBaseSchema):
    pass


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = Field(default=None)
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = Field(default=None)
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)


class MovieDetailSchema(MovieBaseSchema):
    id: int
    country: CountryRetrieveSchema
    genres: List[GenreRetrieveSchema]
    actors: List[ActorRetrieveSchema]
    languages: List[LanguageRetrieveSchema]

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    class Config:
        from_attributes = True
