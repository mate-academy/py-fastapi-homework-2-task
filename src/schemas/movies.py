from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date, datetime, timedelta


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]
    model_config = {"from_attributes": True}


class GenreSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieBaseSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date]
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str]
    status: Optional[str]
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    def validate_date(cls, v: Optional[date]):
        if v and v > (datetime.now().date() + timedelta(days=365)):
            raise ValueError("Release date cannot be more than one year in the future")
        return v

    @field_validator("status")
    def validate_status(cls, v: Optional[str]):
        if v is None:
            return v
        allowed_statuses = {"Released", "Post Production", "In Production"}
        if v not in allowed_statuses:
            raise ValueError(
                "Status must be one of: Released, Post Production, In Production."
            )
        return v


class MovieCreateSchema(MovieBaseSchema):
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)



class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Optional[CountrySchema]
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = {"from_attributes": True}
