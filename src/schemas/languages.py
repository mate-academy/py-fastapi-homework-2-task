from pydantic import BaseModel


class LanguageDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
