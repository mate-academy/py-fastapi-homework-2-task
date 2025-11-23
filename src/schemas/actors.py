from typing import List
from pydantic import BaseModel
from src.schemas.movies import MovieDetail


class ActorBase(BaseModel):
    name: str


class ActorCreate(ActorBase):
    pass


class ActorUpdate(ActorBase):
    pass


class ActorRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
