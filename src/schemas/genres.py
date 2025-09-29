from pydantic import BaseModel


class GenreSchema(BaseModel):
    name: str


class GenreResponseSchema(GenreSchema):
    id: int
    model_config = {
        "from_attributes": True,
    }
