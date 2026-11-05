import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: Optional[str] = None


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator('date')
    @classmethod
    def date_not_too_far_in_future(cls, v: datetime.date) -> datetime.date:
        max_date = datetime.date.today() + datetime.timedelta(days=365)
        if v > max_date:
            raise ValueError('Date cannot be more than one year in the future')
        return v


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    @field_validator('date')
    @classmethod
    def date_not_too_far_in_future(cls, v: Optional[datetime.date]) -> Optional[datetime.date]:
        if v is not None:
            max_date = datetime.date.today() + datetime.timedelta(days=365)
            if v > max_date:
                raise ValueError('Date cannot be more than one year in the future')
        return v
