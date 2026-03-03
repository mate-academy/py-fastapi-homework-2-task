from pydantic import BaseModel


class ActorResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorCreateSchema(BaseModel):
    name: str
