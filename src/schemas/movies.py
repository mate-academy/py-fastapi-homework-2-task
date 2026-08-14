from datetime import date as Date, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class GenreRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountryRead(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class LanguageRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: Date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: Date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum = MovieStatusEnum.RELEASED
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: Date) -> Date:
        if value > Date.today() + timedelta(days=365):
            raise ValueError(
                "Release date must not be more than one year in the future."
            )

        return value


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: Date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    country: CountryRead
    genres: list[GenreRead]
    actors: list[ActorRead]
    languages: list[LanguageRead]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: Date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, value: Date | None) -> Date | None:
        if value is not None and value > Date.today() + timedelta(days=365):
            raise ValueError(
                "Release date must not be more than one year in the future."
            )

        return value
