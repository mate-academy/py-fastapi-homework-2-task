import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field
from pydantic_extra_types.country import CountryAlpha2, CountryAlpha3


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class BaseSchema(BaseModel):
    id: int
    name: str


class Country(BaseModel):
    id: int
    code: str
    name: str | None


class Genre(BaseSchema):
    pass


class Actor(BaseSchema):
    pass


class Language(BaseSchema):
    pass


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field(
        le=datetime.date.today() + datetime.timedelta(days=365)
    )
    score: float = Field(ge=0, le=100, description="float (0-100)")
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieRead(MovieBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    movies: List[MovieRead]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(MovieBase):
    status: MovieStatusEnum = Field(
        description="string (Released | Post Production | In Production)"
    )
    budget: float = Field(ge=0 ,description="float (>= 0)")
    revenue: float = Field(ge=0, description="float (>= 0)")
    country: CountryAlpha2 | CountryAlpha3 = Field(
        description="string (ISO 3166-1 alpha-2 code)"
    )
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = ConfigDict(from_attributes=True)


class MovieDetail(MovieBase):
    id: int
    status: MovieStatusEnum = Field(
        description="string (Released | Post Production | In Production)"
    )
    budget: float = Field(ge=0 ,description="float (>= 0)")
    revenue: float = Field(ge=0, description="float (>= 0)")
    country: Country
    genres: List[Genre]
    actors: List[Actor]
    languages: List[Language]
