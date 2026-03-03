import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Country(BaseModel):
    id: int
    code: str
    name: str | None


class Actor(BaseModel):
    id: int
    name: str


class Genre(BaseModel):
    id: int
    name: str


class Language(BaseModel):
    id: int
    name: str


class Movie(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, date_v: datetime.date):
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if date_v > max_date:
            raise ValueError(
                "Date cannot be more than one year in the future"
            )
        return date_v


class MovieCreateSchema(MovieBase):
    country: str
    actors: list[str]
    genres: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: str | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, date_v: datetime.date | None):
        if date_v is None:
            return date_v
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if date_v > max_date:
            raise ValueError(
                "Date cannot be more than one year in the future"
            )
        return date_v


class MovieDetailSchema(MovieBase):
    id: int

    country: Country
    actors: list[Actor]
    genres: list[Genre]
    languages: list[Language]

    model_config = ConfigDict(from_attributes=True)


class MovieListSchema(BaseModel):
    movies: list[Movie]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int
