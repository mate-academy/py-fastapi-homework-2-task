from pydantic import (
    BaseModel,

    PositiveInt
)


class GenderBaseSchema(BaseModel):
    name: str


class GenderReadSchema(GenderBaseSchema):
    id: PositiveInt
