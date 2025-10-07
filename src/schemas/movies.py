from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    Released = "Released"
    Post_Production = "Post Production"
    In_Production = "In Production"


class GenreBaseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorBaseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CountryBaseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = {"from_attributes": True}


class LanguageBaseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieBaseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListItemSchema(MovieBaseSchema):
    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    total_items: int
    total_pages: int
    prev_page: Optional[str]
    next_page: Optional[str]


class MovieDetailSchema(MovieBaseSchema):
    score: float
    status: StatusEnum
    budget: float
    revenue: float
    country: CountryBaseSchema
    genres: List[GenreBaseSchema]
    actors: List[ActorBaseSchema]
    languages: List[LanguageBaseSchema]

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: StatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = {"from_attributes": True}


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[StatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    model_config = {"from_attributes": True}
