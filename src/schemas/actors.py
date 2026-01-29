from pydantic import BaseModel


class ActorBaseSchema(BaseModel):
    id: int
    name: str
