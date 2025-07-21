import datetime
from typing import Generic, TypeVar, List, Optional, Annotated

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, AnyHttpUrl, constr, AfterValidator, confloat

from database.models import MovieStatusEnum

M = TypeVar("M")


def validate_date_no_more_than_one_year_from_now(
    date: datetime.date,
) -> Optional[datetime.date]:
    today = datetime.date.today()
    if date > today + datetime.timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    return date


class IdNameBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CountryReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str]


class GenreReadSchema(IdNameBaseSchema):
    pass


class ActorReadSchema(IdNameBaseSchema):
    pass


class LanguageReadSchema(IdNameBaseSchema):
    pass


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel, Generic[M]):
    movies: List[M]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryReadSchema
    genres: list[GenreReadSchema]
    actors: list[ActorReadSchema]
    languages: list[LanguageReadSchema]


class MovieCreateSchema(BaseModel):
    name: constr(min_length=1, max_length=255)
    date: Annotated[
        datetime.date, AfterValidator(validate_date_no_more_than_one_year_from_now)
    ]
    score: confloat(ge=0.0, le=100.0)
    overview: str
    status: MovieStatusEnum
    budget: confloat(ge=0.0)
    revenue: confloat(ge=0.0)
    country: constr(min_length=3, max_length=3, to_upper=True)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)] = None
    date: Optional[
        Annotated[
            datetime.date, AfterValidator(validate_date_no_more_than_one_year_from_now)
        ]
    ] = None
    score: Optional[confloat(ge=0.0, le=100.0)] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[confloat(ge=0.0)] = None
    revenue: Optional[confloat(ge=0.0)] = None
