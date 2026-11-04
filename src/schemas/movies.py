import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)

from database.models import MovieStatusEnum


def validate_year_date(val_date: datetime.date | None):
    if val_date is not None and val_date > datetime.date.today() + datetime.timedelta(days=365):
        raise ValueError("Date cannot be more than one year in the future")
    return val_date


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, val_date):
        return validate_year_date(val_date)


class MovieListItemSchema(MovieBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieCreateSchema(MovieBaseSchema):
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, val_date):
        return validate_year_date(val_date)
