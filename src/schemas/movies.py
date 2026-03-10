import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CountrySchema(BaseModel):
    id: int
    name: Optional[str] = None
    code: str

    class Config:
        from_attributes = True


class NameSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


GenreSchema = NameSchema
ActorSchema = NameSchema
LanguageSchema = NameSchema


class MovieListElement(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MoviePaginationResponse(BaseModel):
    movies: list[MovieListElement]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieBase(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    @classmethod
    def validate_date_not_too_far_in_future(cls, v: datetime.date):
        today = datetime.date.today()

        try:
            one_year_from_now = today.replace(year=today.year + 1)
        except ValueError:
            one_year_from_now = today + datetime.timedelta(days=365)

        if v > one_year_from_now:
            raise ValueError("The date must not be more than one year in the future.")

        return v


class MovieCreate(MovieBase):
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetail(MovieBase):
    id: int
    country: Optional[CountrySchema] = None
    genres: list[GenreSchema] = []
    actors: list[ActorSchema] = []
    languages: list[LanguageSchema] = []

    class Config:
        from_attributes = True


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
