from pydantic import BaseModel, ConfigDict


class ActorBase(BaseModel):
    name: str


class ActorRead(ActorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ActorCreate(ActorBase):
    pass
