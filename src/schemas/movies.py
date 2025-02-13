import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from database.models import MovieStatusEnum


class GenreBaseSchema(BaseModel):
    name: str


class GenreRetrieveSchema(GenreBaseSchema):
    id: int

    class Config:
        from_attributes = True


class ActorBaseSchema(BaseModel):
    name: str


class ActorRetrieveSchema(ActorBaseSchema):
    id: int

    class Config:
        from_attributes = True


class CountryBaseSchema(BaseModel):
    code: str
    name: str | None


class CountryRetrieveSchema(CountryBaseSchema):
    id: int

    class Config:
        from_attributes = True


class LanguageBaseSchema(BaseModel):
    name: str


class LanguageRetrieveSchema(LanguageBaseSchema):
    id: int

    class Config:
        from_attributes = True


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field(
        le=datetime.date.today() + datetime.timedelta(days=365)
    )
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)


class MovieCreateSchema(MovieBaseSchema):
    country: str = Field(pattern=r"^[A-Z]{2}$")
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieRetrieveSchema(MovieBaseSchema):
    id: int
    country: CountryRetrieveSchema
    genres: list[GenreRetrieveSchema]
    actors: list[ActorRetrieveSchema]
    languages: list[LanguageRetrieveSchema]

    class Config:
        from_attributes = True


class MovieShortSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date = Field(
        le=datetime.date.today() + datetime.timedelta(days=365)
    )
    score: float = Field(ge=0, le=100)
    overview: str

    class Config:
        from_attributes = True


class MovieListSchema(BaseModel):
    movies: list[MovieShortSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = Field(
        None,
        le=datetime.date.today() + datetime.timedelta(days=365)
    )
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
