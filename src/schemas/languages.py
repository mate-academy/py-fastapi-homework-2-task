from pydantic import BaseModel, ConfigDict


class LanguageListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
