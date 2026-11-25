from pydantic import BaseModel, ConfigDict


class LanguageBase(BaseModel):
    name: str


class LanguageRead(LanguageBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LanguageCreate(LanguageBase):
    pass
