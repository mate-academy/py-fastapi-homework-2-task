import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    ValidationError
)
from iso3166 import countries

from src.database.models import MovieStatusEnum


class CountryBaseSchema(BaseModel):
    id: int
    code: str
    name: str | None
    model_config = ConfigDict(from_attributes=True)


class GenreBaseSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class ActorBaseSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class LanguageBaseSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieBaseSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str


class MovieListItemSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieBaseSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryBaseSchema
    genres: list[GenreBaseSchema]
    actors: list[ActorBaseSchema]
    languages: list[LanguageBaseSchema]


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date", mode="before")
    @classmethod
    def more_than_one_year_in_future(cls, value: datetime.date | str) -> datetime.date:
        if isinstance(value, str):
            value = datetime.datetime.strptime(value, "%Y-%m-%d").date()

        now = datetime.datetime.now()
        if value.year - now.year > 1:
            raise ValueError("Date must be more than one year in future")

        return value

    @field_validator("country", mode="before")
    @classmethod
    def match_to_iso3166(cls, value: str) -> str:
        if not countries.get(value):
            raise ValueError(
                "Country does not match the iso3166-1 alpha-3 code"
            )

        return value


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(max_length=255, default=None)
    date: datetime.date | None = None
    score: float = Field(ge=0, le=100, default=None)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float = Field(ge=0, default=None)
    revenue: float = Field(ge=0, default=None)
