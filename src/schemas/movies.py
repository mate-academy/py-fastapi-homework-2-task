from pydantic import BaseModel, Field, condecimal
from typing import List, Optional
from datetime import date
from enum import Enum


# --- Перерахування ---
class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


# --- Допоміжні схеми ---
class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        orm_mode = True

class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# --- Схема фільму для списку ---
class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        orm_mode = True

class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


# --- Схема повної інформації про фільм ---
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
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        orm_mode = True


# --- Схема створення фільму ---
class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: condecimal(max_digits=15, decimal_places=2)
    revenue: float
    country_id: int
    genre_ids: List[int] = []
    actor_ids: List[int] = []
    language_ids: List[int] = []


# --- Схема оновлення фільму ---
class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[condecimal(max_digits=15, decimal_places=2)] = None
    revenue: Optional[float] = None
    country_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    actor_ids: Optional[List[int]] = None
    language_ids: Optional[List[int]] = None
