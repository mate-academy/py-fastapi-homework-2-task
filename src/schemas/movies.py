import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def date_not_too_far_future(cls, value):
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str | None


class GenresSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguagesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieCreateResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: CountrySchema
    genres: list[GenresSchema]
    actors: list[ActorsSchema]
    languages: list[LanguagesSchema]

    @field_validator("date")
    @classmethod
    def date_not_too_far_future(cls, value):
        max_date = datetime.date.today() + datetime.timedelta(days=365)

        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")

        return value


class MovieDetailResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenresSchema]
    actors: list[ActorsSchema]
    languages: list[LanguagesSchema]


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def date_not_too_far_future(cls, value):
        max_date = datetime.date.today() + datetime.timedelta(days=365)

        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")

        return value
