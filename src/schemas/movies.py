from datetime import date
from typing import Optional, List

from pydantic import BaseModel, Field

from database.models import MovieStatusEnum


class MovieBase(BaseModel):
    name: str = Field(None, max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str


class MovieListItemSchema(MovieBase):
    id: int

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: Optional[int] = None
    total_items: Optional[int] = None


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


class MovieCreateSchema(MovieBase):
    status: MovieStatusEnum
    budget: float = Field(None, ge=0)
    revenue: float = Field(None, ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class GenreBase(BaseModel):
    name: str


class GenreReadSchema(GenreBase):
    id: int

    class Config:
        from_attributes = True


class GenreCreateSchema(GenreBase):
    pass


class ActorReadSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CountryBase(BaseModel):
    code: str
    name: Optional[str]


class CountryReadSchema(CountryBase):
    id: int

    class Config:
        from_attributes = True


class CountryCreateSchema(CountryBase):
    pass


class LanguageReadSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieDetailSchema(MovieListItemSchema):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryReadSchema
    genres: List[GenreReadSchema]
    actors: List[ActorReadSchema]
    languages: List[LanguageReadSchema]

    class Config:
        from_attributes = True
