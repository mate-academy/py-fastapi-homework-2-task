import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, ConfigDict

from schemas.actors import ActorSchema
from schemas.countries import CountrySchema
from schemas.genres import GenreSchema
from schemas.languages import LanguageSchema


class MovieBaseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(MovieBaseSchema):
    pass


class MovieUpdate(MovieBaseSchema):
    pass


class MoviePatch(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[Literal["Released", "Post Production", "In Production"]] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
    movies: list[MovieListItemSchema]

    model_config = ConfigDict(from_attributes=True)
