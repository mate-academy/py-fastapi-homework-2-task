from pydantic import BaseModel


class LanguageSchema(BaseModel):
    name: str


class LanguageResponseSchema(LanguageSchema):
    id: int
    model_config = {
        "from_attributes": True,
    }
