import datetime
from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field, constr


class MovieStatus(StrEnum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class CountryRead(BaseModel):
    id: int
    code: str
    name: str


class GenreRead(BaseModel):
    id: int
    name: str


class ActorRead(BaseModel):
    id: int
    name: str


class LanguageRead(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    name: str
    date: datetime.datetime
    score: float
    overview: str


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255, min_length=2)
    date: datetime.date = Field(..., alias="date")
    score: float = Field(..., ge=0, le=100, alias="score")
    overview: str = Field(..., min_length=20, max_length=2000)
    status: MovieStatus
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: constr(pattern=r"^[A-Z]{3}$")
    genres: List[str] = Field(..., min_length=1, max_length=12)
    actors: List[str] = Field(..., min_length=1, max_length=20)
    languages: List[str] = Field(..., min_length=1, max_length=20)


class MovieUpdate(MovieBase):
    name: Optional[str] = None
    date: Optional[datetime.datetime] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: MovieStatus = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    class Config:
        from_attributes = True
        extra = "forbid"
        validate_assignment = True


class MovieListItem(BaseModel):  # для списку
    id: int
    name: str
    date: datetime.datetime
    score: float
    overview: str

    class Config:

        from_attributes = True

class MovieDetailRead(MovieBase):
    id: int
    status: str
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True


class MovieDeleteResponse(MovieBase):
    pass
