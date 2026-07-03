import datetime
from pydantic import BaseModel, ConfigDict


class CountryBase(BaseModel):
    code: str
    name: str | None = None


class CountryCreate(CountryBase):
    pass


class CountryUpdate(CountryBase):
    pass


class Country(CountryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GenreBase(BaseModel):
    name: str


class GenreCreate(GenreBase):
    pass


class GenreUpdate(GenreBase):
    pass


class Genre(GenreBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ActorBase(BaseModel):
    name: str


class ActorCreate(ActorBase):
    pass


class ActorUpdate(ActorBase):
    pass


class Actor(ActorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LanguageBase(BaseModel):
    name: str


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(LanguageBase):
    pass


class Language(LanguageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieBase(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float


class MovieCreate(MovieBase):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdate(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None
    status: str | None = None
    budget: float | None = None
    revenue: float | None = None


class MovieDelete(MovieBase):
    pass


class MovieDetailSchema(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: Country
    genres: list[Genre]
    actors: list[Actor]
    languages: list[Language]


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
