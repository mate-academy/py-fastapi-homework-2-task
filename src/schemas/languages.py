from pydantic import BaseModel


class LanguageSchema(BaseModel):
    name: str


class LanguageDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
