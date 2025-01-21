import datetime

from pydantic import BaseModel, Field


class MovieSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float
    overview: str


class MoviesSchema(BaseModel):
    movies: list[MovieSchema]
    prev_page: str | None = Field(max_length=255)
    next_page: str | None = Field(max_length=255)
    total_pages: int
    total_items: int


class GenreSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)


class ActorSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)


class LanguageSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)


class CountrySchema(BaseModel):
    id: int
    code: str = Field(max_length=255)
    name: str | None = Field(max_length=255, default=None)


class MovieDetailSchema(MovieSchema):
    status: str = Field(max_length=255)
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateSchema(BaseModel):
    name: str
    date: datetime.date
    overview: str
    status: str
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]
    score: float = Field(ge=0, le=100)
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    overview: str | None = None
    status: str | None = None
    country: str | None = None
    genres: list[str] | None = None
    actors: list[str] | None = None
    languages: list[str] | None = None
    score: float | None = Field(None, ge=0, le=100)
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)
