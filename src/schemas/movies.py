from pydantic import BaseModel, root_validator, validator
from typing import List, Optional
from datetime import datetime, date


class MovieResponse(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        orm_mode = True
        from_attributes = True


class PaginatedMoviesResponse(BaseModel):
    movies: List[MovieResponse]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class CountryResponse(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class GenreResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class ActorResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class LanguageResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class MovieCreateRequest(BaseModel):
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

    @validator('date', pre=True)
    def parse_date(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {value}. "
                    f"Expected format: YYYY-MM-DD."
                )
        return value


class MovieCreateResponse(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponse
    genres: List[GenreResponse]
    actors: List[ActorResponse]
    languages: List[LanguageResponse]

    class Config:
        orm_mode = True
        from_attributes = True

    @root_validator(pre=True)
    def convert_null_to_string(cls, values):
        country = values.get("country")
        if not country["name"]:
            country["name"] = "null"

        return values


class MovieUpdateRequest(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
