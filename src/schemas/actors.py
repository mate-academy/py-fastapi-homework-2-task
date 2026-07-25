from pydantic import BaseModel


class ActorDetailSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
