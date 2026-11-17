import datetime

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

from pagination.schemas import BaseListPaginationSchema


class MovieStatusChoices(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class MovieListObjectResponse(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseListPaginationSchema):
    movies: list[MovieListObjectResponse]


class MovieCreateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusChoices
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="ISO 3166-1 alpha-3 country code",
    )
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieCountrySchema(BaseModel):
    id: int
    code: str
    name: str | None = None


class MovieGenreSchema(BaseModel):
    id: int
    name: str


class MovieActorSchema(BaseModel):
    id: int
    name: str


class MovieLanguageSchema(BaseModel):
    id: int
    name: str


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: MovieCountrySchema
    genres: list[MovieGenreSchema]
    actors: list[MovieActorSchema]
    languages: list[MovieLanguageSchema]

    model_config = ConfigDict(from_attributes=True)

