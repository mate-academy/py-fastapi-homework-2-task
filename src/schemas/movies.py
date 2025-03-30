from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator
import datetime

from database.models import MovieStatusEnum
from iso3166 import countries


class GenreBaseSchema(BaseModel):
    name: Annotated[str, Field(..., max_length=255)]


class GenreSchema(GenreBaseSchema):
    id: int


class GenreCreateSchema(GenreBaseSchema):
    pass


class ActorBaseSchema(BaseModel):
    name: Annotated[str, Field(..., max_length=255)]


class ActorCreateSchema(ActorBaseSchema):
    pass


class ActorSchema(ActorBaseSchema):
    id: int


class LanguageBaseSchema(BaseModel):
    name: Annotated[str, Field(..., max_length=255)]


class LanguageCreateSchema(LanguageBaseSchema):
    pass


class LanguageSchema(LanguageBaseSchema):
    id: int


# class CountryBaseSchema(BaseModel):
#     code: Annotated[str, Field(..., max_length=3)]
#     name: Annotated[Optional[str], Field(max_length=255)] = None


class CountryCreateSchema(BaseModel):
    code: Annotated[str, Field(..., max_length=3)]
    name: Annotated[Optional[str], Field(max_length=255)] = None


class CountrySchema(BaseModel):
    id: int
    code: Annotated[str, Field(..., max_length=3)]
    name: Annotated[Optional[str], Field(max_length=255)] = None


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum  #######
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


max_date = datetime.datetime.now() + datetime.timedelta(days=365)


class MoviePostRequestSchema(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    date: Annotated[datetime.date, Field(le=max_date.date())]
    score: Annotated[float, Field(ge=0, le=100)]
    overview: str
    status: MovieStatusEnum
    budget: Annotated[float, Field(gt=0)]
    revenue: Annotated[float, Field(gt=0)]
    country: str = Field(..., min_length=3, max_length=3)
    genres: list[str]
    actors: list[str]
    languages: list[str]

    # Валідація для country за допомогою iso3166

    # @field_validator("country", mode="after")
    # @classmethod
    # def validate_country_code(cls, name):
    #     # Перевіряємо, чи є код країни в списку підтримуваних ISO 3166-1 alpha-3
    #     try:
    #         country = countries.get(name)
    #         if country.alpha3 != name:
    #             raise KeyError
    #         return country.alpha3, country.name
    #     except KeyError:
    #         raise ValueError(
    #             f"{name} is not a valid ISO 3166-1 alpha-3 country code"
    #         )


########################################################################


class MoviePostResponseSchema(BaseModel):
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

    model_config = {"from_attributes": True}


############################################################################


class MovieCreateSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float


class MovieUpdateSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: Annotated[float, Field(gt=0)]
    revenue: float
