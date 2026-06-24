import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CountryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str | None = None


class GenreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., description="ISO 3166-1 alpha-3 code")
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: datetime.date) -> datetime.date:
        max_future_year = datetime.datetime.now().year + 1
        if v.year > max_future_year:
            raise ValueError("The date must not be more than one year in the future.")
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
    country: CountryResponse | None = None
    genres: list[GenreResponse]
    actors: list[ActorResponse]
    languages: list[LanguageResponse]


class MovieUpdateRequestSchema(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: str | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: datetime.date | None) -> datetime.date | None:
        if v is not None:
            max_future_year = datetime.datetime.now().year + 1
            if v.year > max_future_year:
                raise ValueError("The date must not be more than one year in the future.")
        return v
