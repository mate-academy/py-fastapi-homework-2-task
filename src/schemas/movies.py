import datetime

from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class GenreResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorsResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguagesResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListReadResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListReadResponseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field(le=datetime.date.today() + datetime.timedelta(days=365))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3, description="ISO 3166-1 alpha-3 code")
    genres: list[str]
    actors: list[str]
    languages: list[str]

    model_config = ConfigDict(from_attributes=True)


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorsResponseSchema]
    languages: list[LanguagesResponseSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(MovieCreateResponseSchema):
    pass


class MovieUpdateRequestSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = Field(None, le=datetime.date.today() + datetime.timedelta(days=365))
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
