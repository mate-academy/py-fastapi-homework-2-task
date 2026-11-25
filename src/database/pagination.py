from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=20)


PaginationHelper = Annotated[Pagination, Query()]
