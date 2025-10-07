import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class IDSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int


class NameSchema(IDSchema):
    name: str


class MovieBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float = Field(..., ge=0, le=100)
    overview: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date):
        today = datetime.date.today()
        one_year_later = today + datetime.timedelta(days=365)
        if value > one_year_later:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieListItemSchema(MovieBaseSchema, IDSchema):
    pass


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int


class MovieBaseCreateSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)


class CountrySchema(IDSchema):
    code: str
    name: str | None = None


class GenresSchema(NameSchema):
    pass


class ActorsSchema(NameSchema):
    pass


class LanguagesSchema(NameSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MovieCreateRequestSchema(MovieBaseCreateSchema):
    country: str = Field(..., max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetailSchema(MovieBaseCreateSchema, IDSchema):
    country: CountrySchema
    genres: list[GenresSchema]
    actors: list[ActorsSchema]
    languages: list[LanguagesSchema]


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=255)
    date: datetime.date | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime.date):
        today = datetime.date.today()
        one_year_later = today + datetime.timedelta(days=365)
        if value > one_year_later:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieUpdateResponseSchema(BaseModel):
    detail: str
