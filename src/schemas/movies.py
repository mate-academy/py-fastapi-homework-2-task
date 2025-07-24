from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import datetime


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: Optional[datetime.date]
    score: int
    overview: str
    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: Optional[int] = None
    total_items: Optional[int] = None


class GenreResponseSchema(BaseModel):
    id: int
    name: str


class ActorResponseSchema(BaseModel):
    id: int
    name: str


class LanguageResponseSchema(BaseModel):
    id: int
    name: str


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str]


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str = Field(..., pattern="^(Released|Post Production|In Production)$")
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date", mode="after")
    def date_validation(cls, value: Optional[datetime.date]):
        if value:
            today = datetime.date.today()
            max_allowed_date = today + datetime.timedelta(days=365)
            if value > max_allowed_date:
                raise ValueError("Date cannot be more than one year in the future")
        return value


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: Optional[datetime.date]
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponseSchema
    genres: List[GenreResponseSchema]
    actors: List[ActorResponseSchema]
    languages: List[LanguageResponseSchema]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = Field(
        default=None, pattern="^(Released|Post Production|In Production)$"
    )
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
