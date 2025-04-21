from pydantic import BaseModel, ConfigDict


class GenreResponseSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GenreAddedSchema(BaseModel):
    name: str
