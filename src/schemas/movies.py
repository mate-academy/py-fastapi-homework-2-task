import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from database.models import MovieStatusEnum


class CountryRead(BaseModel):
    id: int
    code: str = Field(
        min_length=2,
        max_length=3,
        description="ISO 3166-1 alpha-3 country code (e.g., UKR, USA)",
        examples=["UKR"]
    )
    name: Optional[str] = None


class GenreRead(BaseModel):
    id: int
    name: str


class ActorRead(BaseModel):
    id: int
    name: str


class LanguageRead(BaseModel):
    id: int
    name: str


class MovieDetailSchema(BaseModel):
    id: int
    name: str = Field
    date: datetime.date
    score: float = Field
    overview: str
    status: MovieStatusEnum = Field(
        description="The current stage of the project",
        examples=["Released"]
    )
    budget: float
    revenue: float
    country: CountryRead
    genres: List[GenreRead]
    actors: List[ActorRead]
    languages: List[LanguageRead]

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=55)
    date: datetime.date
    score: Decimal = Field(ge=0, le=100, decimal_places=2)
    overview: str = Field(
        examples=["After dominating the boxing world, "
                  "Adonis Creed has been thriving in "
                  "both his career and family life..."]
    )
    status: MovieStatusEnum = Field(
        description="The current stage of the project",
        examples=["Released"]
    )
    budget: Decimal = Field(
        ge=0,
        description="Total project budget (must be 0 or greater)",
        examples=[1000000.0],
        decimal_places=2
    )
    revenue: Decimal = Field(
        ge=0,
        description="Total project revenue (must be 0 or greater)",
        examples=[2500000.0],
        decimal_places=2
    )
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = ConfigDict(from_attributes=True, coerce_numbers_to_str=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float
    overview: str = Field(
        examples=["After dominating the boxing world, "
                  "Adonis Creed has been thriving in "
                  "both his career and family life..."]
    )


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]

    total_items: int = Field(description="Total number of movies")
    total_pages: int = Field(description="Total pages")

    prev_page: Optional[str] = Field(None, examples=["http://api.com/v1/movies?page=1"])
    next_page: Optional[str] = Field(None, examples=["http://api.com/v1/movies?page=3"])

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "movies": [{"id": 1, "name": "Inception", "date": "2010-10-10", "genre": "Drama"}],
                "total_items": 100,
                "total_pages": 10,
                "prev_page": None,
                "next_page": "http://api.com/v1/movies?page=2"
            }
        }
    )


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
