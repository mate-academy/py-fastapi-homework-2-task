from pydantic import BaseModel, ConfigDict


class LanguageResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageAddedSchema(BaseModel):
    name: str
