from pydantic import (
    BaseModel,
    model_validator,
    Field,
    condecimal,
)
from typing import List, Optional
from datetime import date, datetime, timedelta


class CountryBase(BaseModel):
    id: int
    code: str
    name: str | None


class GenreBase(BaseModel):
    id: int
    name: str


class ActorBase(BaseModel):
    id: int
    name: str


class LanguageBase(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    id: int
    name: str = Field(..., max_length=255, description="Invalid input data.")
    date: date
    score: condecimal(ge=0, le=100)
    overview: str

    @model_validator(mode="after")
    def convert_score(cls, values):
        values.score = float(values.score)
        return values


class MovieCreate(MovieBase):
    id: Optional[int] = None
    status: str
    budget: condecimal(ge=0)
    revenue: condecimal(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @model_validator(mode="after")
    def validate_release_date(cls, values):
        if values.date > (datetime.now().date() + timedelta(days=365)):
            raise ValueError(
                "The release date must not be more than one year in the future."
            )
        return values

    class Config:
        from_attributes = True
        orm_mode = True


class MovieDetail(MovieBase):
    status: str
    budget: float
    revenue: float
    country: CountryBase
    genres: List[GenreBase]
    actors: List[ActorBase]
    languages: List[LanguageBase]


class MovieListResponseSchema(BaseModel):
    movies: List[MovieBase]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int | None = None
    total_items: int