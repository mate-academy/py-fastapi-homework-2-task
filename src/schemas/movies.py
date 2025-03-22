from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime, timedelta
from typing import List, Optional

from database.models import MovieStatusEnum, CountryModel


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        from_attributes = True


class GenresSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorsSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguagesSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attribute = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    class Config:
        from_attribute = True


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attribute = True

    @field_validator("date")
    def validate_data(cls, value: date) -> date:  # noqa N805
        current_year = datetime.now().year
        if value.year > current_year + 1:
            raise ValueError(
                f"The year in 'date' cannot be greater "
                f"than {current_year + 1}."
            )
        return value


class MovieDetailSchema(BaseModel):
    id: int  # noqa VNE003
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country_id: int

    country: CountrySchema
    genres: List[GenresSchema]
    actors: List[ActorsSchema]
    languages: List[LanguagesSchema]

    class Config:
        from_attributes = True


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    class Config:
        from_attribute = True
