from typing import Annotated, Optional
from pydantic import BaseModel, Field
import datetime

from database.models import MovieStatusEnum


class GenreBaseSchema(BaseModel):
    name: Annotated[str, Field(..., max_length=255)]


class GenreSchema(GenreBaseSchema):
    id: int

    model_config = {"from_attributes": True}


class GenreCreateSchema(GenreBaseSchema):
    pass


class ActorBaseSchema(BaseModel):
    name: Annotated[str, Field(..., max_length=255)]


class ActorCreateSchema(ActorBaseSchema):
    pass


class ActorSchema(ActorBaseSchema):
    id: int

    model_config = {"from_attributes": True}


class LanguageBaseSchema(BaseModel):
    name: Annotated[str, Field(..., max_length=255)]


class LanguageCreateSchema(LanguageBaseSchema):
    pass


class LanguageSchema(LanguageBaseSchema):
    id: int

    model_config = {"from_attributes": True}


class CountryCreateSchema(BaseModel):
    code: Annotated[
        str,
        Field(..., max_length=3),
    ]
    name: Annotated[Optional[str], Field(max_length=255)] = None


class CountrySchema(BaseModel):
    id: int
    code: Annotated[str, Field(..., max_length=3)]
    name: Annotated[Optional[str], Field(max_length=255)] = None

    model_config = {"from_attributes": True}


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


max_date = datetime.datetime.now() + datetime.timedelta(days=365)


class MoviePostRequestSchema(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    date: Annotated[datetime.date, Field(le=max_date.date())]
    score: Annotated[float, Field(ge=0, le=100)]
    overview: str
    status: MovieStatusEnum
    budget: Annotated[float, Field(gt=0)]
    revenue: Annotated[float, Field(gt=0)]
    country: str = Field(..., max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MoviePostResponseSchema(BaseModel):
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

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float


class MovieUpdateRequestSchema(BaseModel):
    name: Annotated[Optional[str], Field(max_length=255)] = None
    date: Annotated[Optional[datetime.date], Field(le=max_date.date())] = None
    score: Annotated[Optional[float], Field(ge=0, le=100)] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Annotated[Optional[float], Field(gt=0)] = None
    revenue: Annotated[Optional[float], Field(gt=0)] = None
