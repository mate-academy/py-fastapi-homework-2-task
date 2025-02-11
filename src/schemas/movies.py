from datetime import date
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class CountryBase(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class GenreBase(BaseModel):
    id: int
    name: Optional[str] = None


class ActorBase(BaseModel):
    id: int
    name: Optional[str] = None


class LanguageBase(BaseModel):
    id: int
    name: Optional[str] = None


class MovieListBase(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListBase]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: Optional[int] = None
    total_items: Optional[int] = None


class MovieBase(BaseModel):
    name: str
    date: date
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Score must be between 0 and 100."
    )
    overview: str
    status: str = Field(
        ...,
        pattern="^(Released|Post Production|In Production)$"
    )
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)

    class Config:
        from_attributes = True


class MovieCreate(MovieBase):
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True


class MovieDetail(MovieBase):
    id: int
    country: Union[str, CountryBase]
    genres: List[GenreBase | None] = None
    actors: List[ActorBase | None] = None
    languages: List[LanguageBase | None] = None

    class Config:
        from_attributes = True


class MovieUpdate(MovieBase):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Score must be between 0 and 100."
    )
    overview: Optional[str] = None
    status: Optional[str] = Field(
        None,
        pattern="^(Released|Post Production|In Production)$"
    )
    budget: Optional[float] = None
    revenue: Optional[float] = None

    class Config:
        from_attributes = True
