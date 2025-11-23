from typing import List
from pydantic import BaseModel
from src.schemas.movies import MovieDetail


class LanguageBase(BaseModel):
    name: str


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(LanguageBase):
    pass


class LanguageRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
