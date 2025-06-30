from pydantic import BaseModel, condecimal, constr, validator
from datetime import date, timedelta
from typing import List, Optional, Literal
import datetime


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        orm_mode = True


class SimpleEntitySchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class MovieCreateSchema(BaseModel):
    name: constr(max_length=255)
    date: date
    score: condecimal(ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: condecimal(ge=0)
    revenue: condecimal(ge=0)
    country: str
    genre_ids: List[int]
    actor_ids: List[int]
    language_ids: List[int]

    @validator("date")
    def validate_date(cls, value):
        if value > date.today() + timedelta(days=365):
            raise ValueError("Release date can't be more than 1 year in the future.")
        return value


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[SimpleEntitySchema]
    actors: List[SimpleEntitySchema]
    languages: List[SimpleEntitySchema]

    class Config:
        orm_mode = True

class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float

    class Config:
        orm_mode = True

class MovieListResponseSchema(BaseModel):
    total: int
    page: int
    size: int
    items: List[MovieListItemSchema]


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]

    class Config:
        orm_mode = True

class MovieUpdateSchema(BaseModel):
    name: Optional[str]
    date: Optional[datetime.date]
    score: Optional[float]
    overview: Optional[str]
    status: Optional[str]
    budget: Optional[float]
    revenue: Optional[float]
    country_id: Optional[int]
    genre_ids: Optional[list[int]]
    actor_ids: Optional[list[int]]
    language_ids: Optional[list[int]]

    class Config:
        orm_mode = True