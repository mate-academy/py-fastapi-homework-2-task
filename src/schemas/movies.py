from pydantic import BaseModel, Field, field_validator, constr, conlist, condecimal, ConfigDict
from datetime import date, timedelta, datetime
from typing import List, Optional, Literal

class NamedEntity(BaseModel):
    id: int
    name: str

class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    name: constr(max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: condecimal(ge=0)
    revenue: condecimal(ge=0)
    country: constr(min_length=3, max_length=3)
    genres: conlist(str, min_length=1)
    actors: conlist(str, min_length=1)
    languages: conlist(str, min_length=1)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v > datetime.utcnow().date() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return v

class MovieUpdate(BaseModel):
    name: Optional[constr(max_length=255)]
    date: Optional[date]
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str]
    status: Optional[Literal["Released", "Post Production", "In Production"]]
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v > datetime.utcnow().date() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return v

class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[NamedEntity]
    actors: List[NamedEntity]
    languages: List[NamedEntity]

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int
