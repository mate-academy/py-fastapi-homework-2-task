from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

DB = Annotated[AsyncSession, Depends(get_db)]


@dataclass
class PaginationParams:
    page: int
    per_page: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page

    def total_pages(self, total_items: int) -> int:
        return (total_items + self.per_page - 1) // self.per_page

    def build_page_url(self, base_url: str, page: int) -> str:
        return f"{base_url}?page={page}&per_page={self.per_page}"


def pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
) -> PaginationParams:
    return PaginationParams(page=page, per_page=per_page)


PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]
