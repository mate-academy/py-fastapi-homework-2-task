from pydantic import (
    BaseModel,

    PositiveInt
)
from pydantic_extra_types.language_code import (
    LanguageName
)


class LanguageBaseSchema(BaseModel):
    name: str


class LanguageReadSchema(LanguageBaseSchema):
    id: PositiveInt
