# Write your code here
from typing import List, Optional
from pydantic import BaseModel, Field
class GenreModel(BaseModel):
    name: str
    movies: list["MovieDetailSchema"]


class GenreDetail(GenreModel):
    id: int

    class Config:
        from_attributes = True


class GenreDetailResponse(BaseModel):
    id: int
    name: str

