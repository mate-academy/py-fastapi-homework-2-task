from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class GenreBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class ActorBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class CountryBase(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class LanguageBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class MoviesListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        orm_mode = True
        from_attributes = True


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryBase
    languages: list[LanguageBase]
    actors: list[ActorBase]
    genres: list[GenreBase]

    class Confid:
        orm_mode = True
        from_attributes = True


class MoviesListResponseSchema(BaseModel):
    movies: List[MoviesListItemSchema]
    prev_page: Optional[int]
    next_page: Optional[int]
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(..., max_length=155)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str = Field(
        ...,
        pattern="^(Rumored|Planned|In Production|Post\
            Production|Released|Canceled)$")
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country_id: str = Field(..., min_length=2, max_length=2)
    languages: list[str]
    actors: list[str]
    genres: list[str]


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=155)
    date: Optional[date]
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str]
    status: Optional[str] = Field(
        None,
        pattern="^(Rumored|Planned|In Production|Post\
            Production|Released|Canceled)$")
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    country_id: Optional[str] = Field(None, min_length=2, max_length=2)
    languages: Optional[list[str]]
    actors: Optional[list[str]]
    genres: Optional[list[str]]


class MovieDeleteRequestSchema(BaseModel):
    id: int
