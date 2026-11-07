from pydantic import BaseModel


class LanguageBaseSchema(BaseModel):
    name: str | None = None


class LanguageRetrieveSchema(LanguageBaseSchema):
    id: int

    class Config:
        from_attributes = True
