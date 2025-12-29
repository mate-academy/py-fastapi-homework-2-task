import datetime
from typing import Optional

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, AnyUrl, Field, field_validator
from typing_extensions import Annotated

from database.models import MovieStatusEnum

String255 = Annotated[str, Field(max_length=255, description="Max length 255")]
CountryAlpha3 = Annotated[str, Field(max_length=3, min_length=1, pattern=r"^[A-Z]{1,3}$")]
FloatGe0 = Annotated[float, Field(ge=0)]
FloatGe0Le100 = Annotated[float, Field(ge=0, le=100)]


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: String255
    date: datetime.date
    score: FloatGe0Le100
    status: MovieStatusEnum
    overview: str
    budget: FloatGe0
    revenue: FloatGe0
    country: CountryAlpha3
    genres: list[String255]
    actors: list[String255]
    languages: list[String255]

    @field_validator("date", mode="after")
    @classmethod
    def validate_date(cls, value: datetime.date) -> datetime.date:
        now = datetime.datetime.now().date()
        if now + relativedelta(years=1) < value:
            raise ValueError(f"Date {value} is before more than 1 year in future.")
        return value


class CountrySchema(BaseModel):
    id: int
    code: CountryAlpha3
    name: Optional[str] = None


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str


class MovieDetailSchema(BaseModel):
    id: int
    name: String255
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

    model_config = {
        "from_attributes": True
    }


class MovieEditSchema(BaseModel):
    name: Optional[String255] = None
    date: Optional[datetime.date] = None
    score: Optional[FloatGe0Le100] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[FloatGe0] = None
    revenue: Optional[FloatGe0] = None
