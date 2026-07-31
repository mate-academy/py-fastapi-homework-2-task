import datetime

from pydantic import BaseModel, ConfigDict, Field

from fastapi import Request

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None
    model_config = ConfigDict(from_attributes=True)


class MovieDetailItemsBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class GenreSchema(MovieDetailItemsBase):
    pass


class ActorSchema(MovieDetailItemsBase):
    pass


class LanguageSchema(MovieDetailItemsBase):
    pass


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieUpdateSchema(BaseModel):
    name: str = Field(max_length=255, default=255)
    date: datetime.date | None = None
    score: float = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float = Field(default=None, ge=0)
    revenue: float = Field(default=None, ge=0)


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]
    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


def get_pagination_urls(request: Request, page: int, per_page: int, total: int):
    base_url = request.url.path.removeprefix("/api/v1")

    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if (page * per_page) < total
        else None
    )

    return prev_page, next_page
