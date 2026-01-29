from pydantic import BaseModel


class GenreBaseSchema(BaseModel):
    id: int
    name: str
