from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class GenreBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class ActorBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class LanguageBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class CountryBase(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


class MovieModel(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    country = relationship("CountryModel", back_populates="movies")


class MovieBase(BaseModel):
    id: int
    name: str
    date: str
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryBase
    genres: List[GenreBase]
    actors: List[ActorBase]
    languages: List[LanguageBase]

    class Config:
        orm_mode = True
        from_attributes = True


class MovieListItemResponse(BaseModel):
    id: int
    name: str
    date: str
    score: Optional[float] = None
    overview: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


class MovieListResponse(BaseModel):
    movies: List[MovieBase]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int

    class Config:
        orm_mode = True
        from_attributes = True


class MovieCreate(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None


class CountryModel(Base):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)

    def __repr__(self):
        return f"<Country(id={self.id}, name={self.name}, code={self.code})>"


class CountryResponse(BaseModel):
    id: int
    name: str = Field(..., example="USA")
    code: str = Field(..., example="US")


class MovieDetailResponse(BaseModel):
    id: int
    name: str
    date: str
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponse


class MovieStatusEnum(str, Enum):
    released = "released"
    unreleased = "unreleased"
    upcoming = "upcoming"


class MovieResponse(BaseModel):
    id: int
    name: str
    date: str
    score: Optional[float] = None
    overview: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj.date, str):
            try:
                obj.date = datetime.strptime(obj.date, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Invalid date format, expected YYYY-MM-DD")

        elif isinstance(obj.date, date):
            obj.date = obj.date.strftime('%Y-%m-%d')

        return super().model_validate(obj)


class PaginationResponse(BaseModel):
    movies: List[MovieListItemResponse]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int
