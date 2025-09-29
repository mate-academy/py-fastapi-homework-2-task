from pydantic import BaseModel


class ActorSchema(BaseModel):
    name: str


class ActorResponseSchema(ActorSchema):
    id: int
    model_config = {
        "from_attributes": True,
    }
