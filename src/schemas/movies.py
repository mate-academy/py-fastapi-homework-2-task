import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError

from database.models import MovieStatusEnum


class CountryBaseSchema(BaseModel):
    code: str
    name: str | None = None


class CountryDetailSchema(CountryBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GenreBaseSchema(BaseModel):
    name: str


class GenreDetailSchema(GenreBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ActorBaseSchema(BaseModel):
    name: str


class ActorDetailSchema(ActorBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LanguageBaseSchema(BaseModel):
    name: str


class LanguageDetailSchema(LanguageBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateItemSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date):
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError()
        return value


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryDetailSchema
    genres: list[GenreDetailSchema]
    actors: list[ActorDetailSchema]
    languages: list[LanguageDetailSchema]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date):
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError()
        return value
