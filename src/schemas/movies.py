import datetime
from enum import Enum
from typing import List, Optional

from pydantic import (
    BaseModel,
    Field,
    validator
)


class MovieStatusEnum(str, Enum):
    released = "Released"
    post_production = "Post Production"
    filming = "Filming"
    planned = "Planned"


class CountrySchema(BaseModel):
    id: int
    name: Optional[str]
    code: Optional[str]


class MovieBase(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    genres: List[str]
    actors: List[str]
    languages: List[str]


class ItemSchema(BaseModel):
    id: int
    name: str

class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Optional[CountrySchema]
    genres: List[ItemSchema]
    actors: List[ItemSchema]
    languages: List[ItemSchema]


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {
        "from_attributes": True
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=0, max_length=100)
    date: datetime.date = Field()
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @validator("date")
    def date_not_too_far(cls, v):
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if v > max_date:
            raise ValueError('Date cannot be more than 1 year in the future')
        return v


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Optional[CountrySchema]
    genres: List[ItemSchema]
    actors: List[ItemSchema]
    languages: List[ItemSchema]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=0, max_length=100)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @validator("date")
    def date_not_too_far(cls, v):
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if v > max_date:
            raise ValueError('Date cannot be more than 1 year in the future')
        return v
