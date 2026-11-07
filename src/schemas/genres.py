from pydantic import BaseModel


class GenreBaseSchema(BaseModel):
    name: str | None = None


class GenreRetrieveSchema(GenreBaseSchema):
    id: int

    class Config:
        from_attributes = True
