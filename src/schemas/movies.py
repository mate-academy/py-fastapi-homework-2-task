import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str | None = None


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float | int = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float | int = Field(ge=0)
    revenue: float | int = Field(ge=0)
    country: str = Field(min_length=2, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError
        return value


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float | int = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float | int = Field(ge=0)
    revenue: float | int = Field(ge=0)
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieForListSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float | int = Field(ge=0, le=100)
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieForListSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(max_length=255, default=None)
    date: datetime.date | None = None
    score: float | int | None = Field(ge=0, le=100, default=None)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | int | None = Field(ge=0, default=None)
    revenue: float | int | None = Field(ge=0, default=None)
