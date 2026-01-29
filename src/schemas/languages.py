from pydantic import BaseModel


class LanguageBaseSchema(BaseModel):
    id: int
    name: str
