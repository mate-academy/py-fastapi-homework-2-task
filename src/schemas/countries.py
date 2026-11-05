from pydantic import BaseModel, ConfigDict
from pydantic_extra_types.country import CountryAlpha3, CountryAlpha2


class CountryScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: CountryAlpha3 | CountryAlpha2
    name: str | None
