from pydantic import BaseModel


class ActorBase(BaseModel):
    name: str


class ActorCreate(ActorBase):
    pass


class ActorRead(ActorBase):
    id: int

    class Config:
        from_attributes = True
