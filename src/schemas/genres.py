from pydantic import BaseModel


class GenreResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
