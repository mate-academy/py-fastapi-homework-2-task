from pydantic import BaseModel


class CountryBase(BaseModel):
    code: str
    name: str | None = None


class CountryCreate(CountryBase):
    pass


class CountryRead(CountryBase):
    id: int

    class Config:
        from_attributes = True
