from datetime import date

from pydantic import BaseModel, ConfigDict


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    total_pages: int
    total_items: int
    prev_page: str | None
    next_page: str | None


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None


class RelatedItemSchema(BaseModel):
    id: int
    name: str


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
    country: CountrySchema
    genres: list[RelatedItemSchema]
    actors: list[RelatedItemSchema]
    languages: list[RelatedItemSchema]


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    score: float | None = None
