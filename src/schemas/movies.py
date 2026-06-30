# Write your code here


import datetime

from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict

from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0.0, le=100.0)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v.year > datetime.date.today().year + 1:
            raise ValidationError("Date must not be more than 1 year in the future")
        return v


class MovieGenresSchema(BaseModel):
    id: int
    name: str


class MovieActorsSchema(BaseModel):
    id: int
    name: str


class MovieLanguagesSchema(BaseModel):
    id: int
    name: str


class MovieCountrySchema(BaseModel):
    id: int
    code: str
    name: str | None


class MovieCreationDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: MovieCountrySchema
    genres: list[MovieGenresSchema]
    actors: list[MovieActorsSchema]
    languages: list[MovieLanguagesSchema]


class MovieDetailSchema(MovieCreationDetailSchema):
    pass


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
    country: str | None = Field(default=None, max_length=3)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v is not None and v.year > datetime.date.today().year + 1:
            raise ValidationError("Date must not be more than 1 year in the future")
        return v


class DetailMessageSchema(BaseModel):
    detail: str
