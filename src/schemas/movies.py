from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class MovieBase(BaseModel):
    title: str
    genre: str
    price: float


class MovieCreate(MovieBase):
    name: str =  Field(..., max_length=255)
    date: date
    score: float = Field(..., gt=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., gt=0)
    revenue: float = Field(..., gt=0)
    country: str
    genres: List[GenreSchema]
    actors: List[ActorSchema]



class MovieUpdate(MovieBase):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)


class MovieRead(BaseModel):
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
