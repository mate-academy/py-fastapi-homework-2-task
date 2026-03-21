from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import List, Optional


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    def date_check(cls, v):
        limit = datetime.now().date().replace(year=datetime.now().year + 1)
        if v > limit:
            raise ValueError("Date cannot be more than one year in the future")
        return v


MovieCreate = MovieCreateSchema


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


MovieUpdate = MovieUpdateSchema


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

    class Config:
        from_attributes = True


MovieDetailResponse = MovieDetailSchema
MovieDetailResponseSchema = MovieDetailSchema
MovieListItemSchema = MovieDetailSchema  # ТЕ, ЩО ШУКАЮТЬ ТЕСТИ ЗАРАЗ


class MovieListResponseSchema(BaseModel):
    movies: List[MovieDetailSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


MovieListResponse = MovieListResponseSchema
MovieListSchema = MovieListResponseSchema
