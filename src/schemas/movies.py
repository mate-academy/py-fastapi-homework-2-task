from datetime import date as Date, timedelta
from pydantic import (
    BaseModel,
    field_validator,

    Field,
    ConfigDict,
    PositiveFloat,
    PositiveInt
)
from typing_extensions import (
    Annotated
)

from database.models import MovieStatusEnum
from schemas.actors import (
    ActorBaseSchema,
    ActorReadSchema
)
from schemas.genres import (
    GenderBaseSchema,
    GenderReadSchema
)
from schemas.languages import (
    LanguageBaseSchema,
    LanguageReadSchema
)
from schemas.countries import (
    CountryReadSchema
)
from schemas.paginations import (
    PaginationResponseSchema
)


class MovieReadSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: PositiveInt
    name: str
    date: Date
    score: Annotated[
        float,
        Field(ge=0.0, le=100.0, description="Score movie from 1.0 to 10.0")
    ]
    overview: str


class MovieReadPaginatedSchemas(PaginationResponseSchema):
    model_config = ConfigDict(
        from_attributes=True
    )

    movies: list[MovieReadSchema]


class MovieCreateSchema(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    date: Date
    score: Annotated[float, Field(ge=1.0, le=100.0,)]
    overview: str
    status: MovieStatusEnum
    budget: PositiveFloat
    revenue: PositiveFloat
    country: Annotated[str, Field(max_length=3, min_length=2, pattern=r"^[A-Z]{2,3}")]
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @classmethod
    @field_validator("date")
    def validate_date(cls, value: Date):
        """
        Validate that current date is not set more then one year
        in the future
        """
        one_year_later = Date.today() + timedelta(days=365)

        if value > one_year_later:
            raise ValueError(
                "Date must not be more then a year in the future."
                f"Last year date: [{one_year_later}]"
            )
        return value


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: PositiveInt
    name: Annotated[str, Field(max_length=255)]
    date: Date
    score: Annotated[float, Field(ge=1.0, le=100.0,)]
    overview: str
    status: MovieStatusEnum
    budget: PositiveFloat
    revenue: PositiveFloat
    country: CountryReadSchema
    genres: list[GenderReadSchema]
    actors: list[ActorReadSchema]
    languages: list[LanguageReadSchema]


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    name: str | None = Field(default=None, max_length=255)
    date: Date | None = None
    score: float | None = Field(default=None, ge=1.0, le=100.0)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: PositiveFloat | None = None
    revenue: PositiveFloat | None = None
