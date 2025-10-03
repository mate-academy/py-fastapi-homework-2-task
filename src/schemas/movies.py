from enum import Enum

from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieShortSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListSchema(BaseModel):
    movies: List[MovieShortSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {"from_attributes": True}


class CountryBaseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    model_config = {"from_attributes": True}


class GenreBaseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorBaseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class LanguageBaseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class StatusEnum(str, Enum):
    released = "Released"
    post_Production = "Post Production"
    in_Production = "In Production"


class MovieCreateSchema(MovieBaseSchema):
    score: float = Field(ge=0, le=100)
    status: StatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieReadSchema(MovieShortSchema):
    score: float
    status: StatusEnum
    budget: float
    revenue: float
    country: CountryBaseSchema
    genres: List[GenreBaseSchema]
    actors: List[ActorBaseSchema]
    languages: List[LanguageBaseSchema]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[StatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
