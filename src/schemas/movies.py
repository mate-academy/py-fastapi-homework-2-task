from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: Date
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
    date: Date
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
    name: str = Field(max_length=255)
    date: Date | None = None
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: date) -> date:
        today = Date.today()
        max_date = today.replace(year=today.year + 1)

        if value > max_date:
            raise ValueError("Date cannot be more than 1 year in the future.")

        return value


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: Date | None = None
    score: float | None = None
    overview: str | None = None
    status: str | None = None
    budget: float | None = None
    revenue: float | None = None
