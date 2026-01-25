from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List, Optional
from decimal import Decimal
from enum import Enum

# Імпортуємо ваш Enum, щоб використовувати його в схемах
from src.database.models import MovieStatusEnum

# Допоміжні схеми для відображення зв'язків
class GenreRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class ActorRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class CountryRead(BaseModel):
    id: int
    code: str
    name: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class LanguageRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

# Основні схеми для Movie
class MovieBase(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: Decimal
    revenue: float

class MovieCreate(MovieBase):
    country_id: int
    genre_ids: List[int] = []
    actor_ids: List[int] = []
    language_ids: List[int] = []

class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[Decimal] = None
    revenue: Optional[float] = None
    country_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    actor_ids: Optional[List[int]] = None
    language_ids: Optional[List[int]] = None

class MovieRead(MovieBase):
    id: int
    country: CountryRead
    genres: List[GenreRead]
    actors: List[ActorRead]
    languages: List[LanguageRead]

    model_config = ConfigDict(from_attributes=True)
