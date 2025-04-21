from pydantic import BaseModel, ConfigDict


class ActorResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorAddedSchema(BaseModel):
    name: str
