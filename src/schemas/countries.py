from pydantic import BaseModel, ConfigDict


class CountryBase(BaseModel):
    code: str
    name: str | None


class CountryRead(CountryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
