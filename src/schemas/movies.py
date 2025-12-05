from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class GenreOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CountryOut(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        from_attributes = True


class LanguageOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryOut
    genres: List[GenreOut]
    actors: List[ActorOut]
    languages: List[LanguageOut]

    class Config:
        from_attributes = True


class MovieListSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int



class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str = Field(..., pattern=r"^(Released|Post Production|In Production)$")
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)

    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(Released|Post Production|In Production)$")
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
