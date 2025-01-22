import datetime

from pydantic import BaseModel, Field, field_validator


class MovieBase(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date
    score: float
    overview: str


class MoviesBase(BaseModel):
    movies: list[MovieBase]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class GenreBase(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=255)


class ActorBase(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=255)


class LanguageBase(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=255)


class CountryBase(BaseModel):
    id: int
    name: str = Field(default=None, max_length=255)
    code: str = Field(max_length=2)


class MovieCreateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    def validate(cls, value: str | datetime.date):
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieDetailSchema(MovieBase):
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    countries: list[CountryBase]
    genres: list[GenreBase]
    actors: list[ActorBase]
    languages: list[LanguageBase]


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(max_length=255)
    date: datetime.date | None
    score: float | None = Field(ge=0, le=100)
    overview: str | None
    status: str | None
    budget: float | None = Field(ge=0)
    revenue: float | None = Field(ge=0)
    country: str | None
    genres: list[str] | None
    actors: list[str] | None
    languages: list[str] | None
