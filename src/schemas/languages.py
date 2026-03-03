from pydantic import BaseModel


class LanguagesResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
