import datetime

from typing import Optional

from pydantic import BaseModel, field_validator, Field

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(gt=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date", mode="after")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Invalid date, must not be more than one year")
        return value

    class Config:
        from_attributes = True


class MovieCreate(MovieDetailSchema):
    pass


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieUpdateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(default=None, gt=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, gt=0)
    revenue: Optional[float] = Field(default=None, gt=0)
