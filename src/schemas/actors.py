from pydantic import (
    BaseModel,

    PositiveInt
)


class ActorBaseSchema(BaseModel):
    name: str


class ActorReadSchema(ActorBaseSchema):
    id: PositiveInt
