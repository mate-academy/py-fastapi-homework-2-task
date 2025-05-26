from pydantic import BaseModel, ConfigDict


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
