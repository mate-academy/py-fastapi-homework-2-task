from typing import List, Optional
from datetime import date

from pydantic import BaseModel, Field


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True


class GenreResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
        orm_mode = True


class ActorResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
        orm_mode = True


class LanguageResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
        orm_mode = True


class MovieListSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True
        orm_mode = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]

    class Config:
        from_attributes = True
        orm_mode = True


class MovieCreateResponseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str = Field(..., pattern="^(Released|Post Production|In Production)$")
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = Field(
        None, pattern="^(Released|Post Production|In Production)$"
    )
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


class UpdateResponseSchema(BaseModel):
    detail: str
