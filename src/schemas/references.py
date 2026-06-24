from pydantic import BaseModel, ConfigDict


class Country(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class Genre(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Actor(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Language(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
