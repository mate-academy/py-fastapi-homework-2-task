from pydantic import BaseModel


class ActorBaseSchema(BaseModel):
    name: str | None = None


class ActorRetrieveSchema(ActorBaseSchema):
    id: int

    class Config:
        from_attributes = True
