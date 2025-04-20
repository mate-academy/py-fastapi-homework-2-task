from pydantic_extra_types.country import (
    CountryAlpha3,
    CountryAlpha2
)
from pydantic import (
    BaseModel,

    PositiveInt
)
from typing_extensions import Optional


class CountryBaseSchema(BaseModel):
    code: CountryAlpha3 | CountryAlpha2
    name: Optional[str]


class CountryReadSchema(CountryBaseSchema):
    id: PositiveInt
