from typing import List
from pydantic import BaseModel
from src.schemas.movies import MovieDetail


class GenreBase(BaseModel):
    name: str


class GenreCreate(GenreBase):
    pass


class GenreUpdate(GenreBase):
    pass


class GenreRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
