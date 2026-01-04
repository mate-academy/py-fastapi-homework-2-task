import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from database.models import MovieStatusEnum


class GenreBase(BaseModel):
    name: str


class GenreRead(GenreBase):
    id: int


class CountryBase(BaseModel):
    code: str
    name: Optional[str] = None


class CountryRead(CountryBase):
    id: int

    class Config:
        orm_mode = True


class ActorBase(BaseModel):
    name: str


class ActorRead(ActorBase):
    id: int

    class Config:
        orm_mode = True


class LanguageBase(BaseModel):
    name: str


class LanguageRead(LanguageBase):
    id: int

    class Config:
        orm_mode = True


class MovieCreate(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date = Field(lt=datetime.date.today() + datetime.timedelta(days=365))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieRead(MovieCreate):
    id: int
    genres: List[GenreRead]
    country: CountryRead
    actors: List[ActorRead]
    languages: List[LanguageRead]

    class Config:
        orm_mode = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int
    movies: list[MovieListItemSchema]

    class Config:
        orm_mode = True


class MovieDetailSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date = Field(lt=datetime.date.today() + datetime.timedelta(days=365))
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountryRead
    genres: List[GenreRead]
    actors: List[ActorRead]
    languages: List[LanguageRead]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(max_length=255, default=None,)
    date: Optional[datetime.date] = Field(default=None, lt=datetime.date.today() + datetime.timedelta(days=365))
    score: Optional[float] = Field(ge=0, le=100, default=None,)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
