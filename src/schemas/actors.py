from pydantic import BaseModel


class ActorSchema(BaseModel):
    name: str


class ActorDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
