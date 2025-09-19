from datetime import date
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, ConfigDict


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: Annotated[list[MovieListItemSchema], Field()]
    prev_page: Annotated[str | None, Field(default=None)]
    next_page: Annotated[str | None, Field(default=None)]
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: dict
    genres: Annotated[list[dict], Field()]
    actors: Annotated[list[dict], Field()]
    languages: Annotated[list[dict], Field()]


class MovieCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1, max_length=255)]
    date: Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2}$')]
    score: Annotated[float, Field(ge=0.0, le=100.0)]
    overview: Annotated[str, Field(min_length=1, max_length=1000)]
    status: Annotated[str, Field()]
    budget: Annotated[float, Field(ge=0.0)]
    revenue: Annotated[float, Field(ge=0.0)]
    country: Annotated[str, Field(min_length=2, max_length=3)]
    genres: Annotated[list[str], Field(min_length=1)]
    actors: Annotated[list[str], Field(min_length=1)]
    languages: Annotated[list[str], Field(min_length=1)]

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['Released', 'Post Production', 'In Production', 'Planned', 'Canceled']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        from datetime import datetime
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class MovieUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    date: Annotated[str | None, Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')]
    score: Annotated[float | None, Field(default=None, ge=0.0, le=100.0)]
    overview: Annotated[str | None, Field(default=None, min_length=1, max_length=1000)]
    status: Annotated[str | None, Field(default=None)]
    budget: Annotated[float | None, Field(default=None, ge=0.0)]
    revenue: Annotated[float | None, Field(default=None, ge=0.0)]
    country: Annotated[str | None, Field(default=None, min_length=2, max_length=3)]
    genres: Annotated[list[str] | None, Field(default=None, min_length=1)]
    actors: Annotated[list[str] | None, Field(default=None, min_length=1)]
    languages: Annotated[list[str] | None, Field(default=None, min_length=1)]

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        valid_statuses = ['Released', 'Post Production', 'In Production', 'Planned', 'Canceled']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        from datetime import datetime
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
