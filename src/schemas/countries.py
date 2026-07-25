from pydantic import BaseModel, ConfigDict


class CountryDetailSchema(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)

