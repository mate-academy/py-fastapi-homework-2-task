from pydantic import BaseModel


class GenreDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
