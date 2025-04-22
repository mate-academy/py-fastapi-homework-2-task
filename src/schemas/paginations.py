from typing_extensions import Annotated

from pydantic import (
    BaseModel,
    Field,
    NonNegativeInt,
)


class PaginationQuerySchema(BaseModel):
    model_config = {"extra": "forbid"}

    page: Annotated[int, Field(ge=1, default=1)]
    per_page: Annotated[int, Field(ge=1, le=20, default=10)]


class PaginationResponseSchema(BaseModel):
    prev_page: str | None
    next_page: str | None
    total_pages: NonNegativeInt
    total_items: NonNegativeInt
