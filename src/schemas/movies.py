import datetime
from typing import List, Optional, Any


from pydantic import BaseModel, ConfigDict, Field

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str = Field(description="ISO 3166-1 alpha-3")
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CountryCreateSchema(BaseModel):
    code: str
    name: Optional[str] = None


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GenreCreateSchema(BaseModel):
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorCreateSchema(BaseModel):
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageCreateSchema(BaseModel):
    name: str


class MovieSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    total_pages: int
    total_items: int
    prev_page: Optional[str] = None
    next_page: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(MovieSchema):
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieRead(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True


class MovieCreate(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float

    # Field for API request
    country: Optional[str] = None
    genres: List[str] = []
    actors: List[str] = []
    languages: List[str] = []

    # Fields for internal use
    country_code: Optional[str] = None
    genre_ids: List[int] = []
    actor_ids: List[int] = []
    language_ids: List[int] = []
    genre_name: Optional[str] = Field(None, max_length=255)
    actor_name: Optional[str] = Field(None, max_length=255)
    language_name: Optional[str] = Field(None, max_length=255)

    def __init__(self, **data):
        super().__init__(**data)
        # Map country to country_code
        if self.country and not self.country_code:
            self.country_code = self.country


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    # Поля для API запиту
    country: Optional[str] = None
    genres: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    # Внутрішні поля
    country_code: Optional[str] = None
    genre_ids: Optional[List[int]] = None
    actor_ids: Optional[List[int]] = None
    language_ids: Optional[List[int]] = None
    genre_name: Optional[str] = None
    actor_name: Optional[str] = None
    language_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.country and not self.country_code:
            self.country_code = self.country
