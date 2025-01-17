from datetime import date, timedelta
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationError
)
from pydantic_extra_types.country import CountryAlpha3


class StatusEnum(str, Enum):
    Released = "Released"
    PostProduction = "Post Production"
    InProduction = "In Production"


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: StatusEnum
    budget: float = Field(gt=0)
    revenue: float = Field(gt=0)
    country: CountryAlpha3
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def check_date_on_the_future(cls, date: date):
        if date > date.today() + timedelta(days=365):
            raise ValidationError(
                "The date must not be more than one year in the future."
            )
        return date


class MovieUpdateSchema(BaseModel):
    pass


class MovieListSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True
