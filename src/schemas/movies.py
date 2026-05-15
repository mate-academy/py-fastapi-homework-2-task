import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator
)
from iso3166 import countries

from database.models import MovieStatusEnum


class CountryDetailSchema(BaseModel):
    id: int
    code: str
    name: str | None


class GenreDetailSchema(BaseModel):
    id: int
    name: str


class ActorDetailSchema(BaseModel):
    id: int
    name: str


class LanguageDetailSchema(BaseModel):
    id: int
    name: str


class MovieRetrieveSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieDetailSchema(MovieRetrieveSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryDetailSchema
    genres: list[GenreDetailSchema]
    actors: list[ActorDetailSchema]
    languages: list[LanguageDetailSchema]
    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    movies: list[MovieRetrieveSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if len(value) > 255:
            raise ValueError("Field name mustn't exceed 255 characters")

        return value

    @field_validator("date", mode="after")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        if value.year - datetime.datetime.now().year > 1:
            raise ValueError(
                "Field date mustn't be more than one year in the future"
            )

        return value

    @field_validator("score", mode="after")
    @classmethod
    def validate_score(cls, value: float) -> float:
        if not (0 <= value <= 100):
            raise ValueError("Field score must be between 0 and 100")

        return value

    @field_validator("budget", "revenue", mode="after")
    @classmethod
    def validate_budget_and_revenue(cls, value: float) -> float:
        if value < 0:
            raise ValueError(
                "Fields budget and revenue must be non-negative"
            )

        return value

    @field_validator("country", mode="after")
    @classmethod
    def validate_country(cls, value: str) -> str:
        if value not in countries:
            raise ValueError("There is no any country by this name")

        return value


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = None
    revenue: float | None = None

    @field_validator("score", mode="after")
    @classmethod
    def validate_score(cls, value: float) -> float:
        if value not in range(0, 101):
            raise ValueError("Field score must be between 0 and 100")

        return value

    @field_validator("budget", "revenue", mode="after")
    @classmethod
    def validate_budget_and_revenue(cls, value: float) -> float:
        if value < 0:
            raise ValueError(
                "Fields budget and revenue must be non-negative"
            )

        return value
