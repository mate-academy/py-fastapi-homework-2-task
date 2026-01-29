from pydantic import BaseModel


class CountryBaseSchema(BaseModel):
    id: int
    code: str
    name: str | None
