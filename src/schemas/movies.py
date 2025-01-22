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


class CountryResponseSchema(BaseSchema):
    code: str
    name: Optional[str]


class GenreResponseSchema(BaseSchema):
    pass


class ActorResponseSchema(BaseSchema):
    pass


class LanguageResponseSchema(BaseSchema):
    pass


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field(
        le=datetime.date.today() + datetime.timedelta(days=365),
        description="The date must not be more than one year in the future."
    )
    score: float = Field(ge=0, le=100, description="float (0-100)")
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieBaseExtra(MovieBase):
    status: MovieStatusEnum = Field(
        description="string (Released | Post Production | In Production)"
    )
    budget: float = Field(ge=0, description="float (>= 0)")
    revenue: float = Field(ge=0, description="float (>= 0)")


class MovieReadResponseSchema(MovieBase):
    id: int


class MovieListResponseSchema(BaseModel):
    movies: List[MovieReadResponseSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(MovieBaseExtra):
    country: CountryAlpha2 | CountryAlpha3 = Field(
        description="string (ISO 3166-1 alpha-2 code)"
    )
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(MovieBaseExtra):
    id: int
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = Field(
        None, le=datetime.date.today() + datetime.timedelta(days=365)
    )
    score: Optional[float] = Field(None, ge=0, le=100, description="float (0-100)")
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = Field(
        None, description="string (Released | Post Production | In Production)"
    )
    budget: Optional[float] = Field(None, ge=0, description="float (>= 0)")
    revenue: Optional[float] = Field(None, ge=0, description="float (>= 0)")
