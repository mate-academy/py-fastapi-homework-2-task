from pydantic import BaseModel


class CountryDetailSchema(BaseModel):
    id: int
    code: str
    name: str | None = None

    class Config:
        from_attributes = True
