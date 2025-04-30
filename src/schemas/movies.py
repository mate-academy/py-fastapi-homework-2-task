from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class MovieDetail(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    prev_page: str | None
    next_page: str | None
    movies: List[MovieBase]

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str = Field(pattern="^(Released|Post Production|In Production)$")
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str = Field(pattern="^[A-Z]{2}$")

    genres: List[str]
    actors: List[str]
    languages: List[str]

    @model_validator(mode="after")
    def validate_date(self) -> "MovieCreate":
        max_date = date.today().replace(year=date.today().year + 1)
        if self.date > max_date:
            raise ValueError("Date cannot be more than one year in the future")

        return self


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = Field(
        default=None, pattern="^(Released|Post Production|In Production)$"
    )
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_date(self) -> "MovieUpdate":
        if self.date:
            max_date = date.today().replace(year=date.today().year + 1)
            if self.date > max_date:
                raise ValueError("Date cannot be more than one year in the future")
        return self
