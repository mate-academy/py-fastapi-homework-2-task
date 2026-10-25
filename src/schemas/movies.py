import datetime

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str = Field(min_length=1, max_length=100)
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        max_date = datetime.date.today() + relativedelta(years=1)

        if value > max_date:
            raise ValueError(
                "Date cannot be more than one year in the future."
            )

        return value


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class NamedEntitySchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[NamedEntitySchema]
    actors: list[NamedEntitySchema]
    languages: list[NamedEntitySchema]

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    date: datetime.date | None = None
    score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    overview: str | None = None
    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    budget: float | None = Field(
        default=None,
        ge=0,
    )
    revenue: float | None = Field(
        default=None,
        ge=0,
    )
