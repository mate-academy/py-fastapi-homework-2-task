from pydantic import (
    BaseModel,

    PositiveInt
)


class GenreBaseSchema(BaseModel):
    name: str


class GenreReadSchema(GenreBaseSchema):
    id: PositiveInt
