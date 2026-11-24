import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class CountryBase(BaseModel):
    code: str = Field(..., max_length=3)
    name: str | None = None


class CountryRead(CountryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GenreBase(BaseModel):
    name: str


class GenreRead(GenreBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ActorBase(BaseModel):
    name: str


class ActorRead(ActorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LanguageBase(BaseModel):
    name: str


class LanguageRead(LanguageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str

    @field_validator("date")
    @classmethod
    def validate_max_future_date(cls, value: datetime.date) -> datetime.date:
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError(
                "The date must not be more than one year in the future."
            )
        return value


class MovieCreateSchema(MovieBase):
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(MovieBase):
    name: str = Field(default=None, max_length=255)
    date: datetime.date = None
    score: float = Field(default=None, ge=0, le=100)
    overview: str = None
    status: MovieStatusEnum = None
    budget: float = Field(default=None, ge=0)
    revenue: float = Field(default=None, ge=0)


class MovieDetailSchema(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: CountryRead
    genres: list[GenreRead]
    actors: list[ActorRead]
    languages: list[LanguageRead]


class MovieListItemSchema(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
