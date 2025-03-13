from datetime import date, timedelta
from typing import List, Optional, Annotated

from pydantic import BaseModel, ConfigDict, Field, AfterValidator
from database.models import MovieStatusEnum

CountryCode = Annotated[str, Field(max_length=3, description="Country Code")]
PositiveFloat = Annotated[float, Field(ge=0.0)]
Score = Annotated[float, Field(ge=0.0, le=100.0)]
Name = Annotated[str, Field(max_length=255)]


def check_date_not_too_far(v: date) -> date:
    max_date = date.today() + timedelta(days=365)
    if v > max_date:
        raise ValueError("The date must not be more than one year in the future")
    return v


MovieDate = Annotated[date, AfterValidator(check_date_not_too_far)]


class GenreBase(BaseModel):
    name: Name

    model_config = ConfigDict(from_attributes=True)


class GenreCreate(GenreBase):
    pass


class Genre(GenreBase):
    id: int


class ActorBase(BaseModel):
    name: Name

    model_config = ConfigDict(from_attributes=True)


class ActorCreate(ActorBase):
    pass


class Actor(ActorBase):
    id: int


class LanguageBase(BaseModel):
    name: Name

    model_config = ConfigDict(from_attributes=True)


class LanguageCreate(LanguageBase):
    pass


class Language(LanguageBase):
    id: int


class CountryBase(BaseModel):
    code: CountryCode
    name: Optional[Name]

    model_config = ConfigDict(from_attributes=True)


class CountryCreate(CountryBase):
    pass


class Country(CountryBase):
    id: int


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: Score
    overview: str
    status: MovieStatusEnum
    budget: PositiveFloat
    revenue: PositiveFloat
    country: Country
    genres: List[Genre]
    actors: List[Actor]
    languages: List[Language]

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: Score
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
    name: str
    date: MovieDate
    score: Score
    overview: str
    status: MovieStatusEnum
    budget: PositiveFloat
    revenue: PositiveFloat
    country: CountryCode
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )


class MovieUpdateSchema(BaseModel):
    name: Optional[Name] = None
    date: Optional[MovieDate] = None
    score: Optional[Score] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[PositiveFloat] = None
    revenue: Optional[PositiveFloat] = None


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number >= 1")
    per_page: int = Field(10, ge=1, le=20, description="Number of movies per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
