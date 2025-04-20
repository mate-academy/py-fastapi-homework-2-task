from pydantic import BaseModel


class GenreSchema(BaseModel):
    name: str


class GenreDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
