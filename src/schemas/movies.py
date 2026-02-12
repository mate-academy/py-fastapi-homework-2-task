import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from database.models import MovieStatusEnum


class GenreSchema(BaseModel):
    name: str


class GenreListSchema(GenreSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ActorSchema(BaseModel):
    name: str


class ActorListSchema(ActorSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CountrySchema(BaseModel):
    code: str
    name: Optional[str] = None


class CountryListSchema(CountrySchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LanguageSchema(BaseModel):
    name: str


class LanguageListSchema(LanguageSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListItemSchema(MovieSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieListItemSchema):
    status: str
    budget: float
    revenue: float
    country: CountryListSchema
    genres: List[GenreListSchema]
    actors: List[ActorListSchema]
    languages: List[LanguageListSchema]


class MovieValidationMixin(BaseModel):
    @field_validator("name", check_fields=False)
    def validate_name(cls, value):
        if len(value) > 255:
            raise ValueError(f"Movie name is too long: {value}")
        return value

    @field_validator("date", check_fields=False)
    def validate_date(cls, value):
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError(
                f"The date must not be more than one year in the future: {value}"
            )
        return value

    @field_validator("score", check_fields=False)
    def validate_score(cls, value):
        if not (0 <= value <= 100):
            raise ValueError(f"Score must be between 0 and 100: {value}")
        return value

    @field_validator("budget", "revenue", check_fields=False)
    def validate_budget_and_revenue(cls, value):
        if value < 0:
            raise ValueError(f"Budget and revenue must be positive: {value}")
        return value


class MovieCreateSchema(MovieSchema):
    budget: float
    revenue: float


class MovieCreateRequestSchema(MovieCreateSchema, MovieValidationMixin):
    status: MovieStatusEnum
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieCreateResponseSchema(MovieCreateSchema):
    id: int
    status: str
    country: CountryListSchema
    genres: List[GenreListSchema]
    actors: List[ActorListSchema]
    languages: List[LanguageListSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieUpdateSchema(MovieValidationMixin):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
