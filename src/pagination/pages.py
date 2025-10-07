from __future__ import annotations
import math
from typing import Any, TypeVar, Generic

from fastapi_pagination.bases import AbstractParams, AbstractPage
from fastapi import Request
from fastapi_pagination.customization import CustomizedPage, UseFieldsAliases

from pagination.params import Params

T = TypeVar("T")


class Page(AbstractPage[T], Generic[T]):
    results: list[T]
    next_page: str | None
    prev_page: str | None
    total_pages: int
    total_items: int

    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: list[T],
        params: AbstractParams,
        *,
        request: Request | None = None,
        total: int | None = None,
        **kwargs: Any
    ) -> Page[T]:
        assert total is not None, "total must be provided"
        assert request is not None, "request must be provided"
        total_pages = math.ceil(total / params.per_page)
        base_path = request.url.path
        if base_path.startswith("/api/v1"):
            base_path = base_path[len("/api/v1"):]
        return cls(
            results=items,
            total_items=total,
            total_pages=total_pages,
            prev_page=(
                f"{base_path}?page={params.page - 1}&per_page={params.per_page}"
                if params.page > 1 else None
            ),
            next_page=(
                f"{base_path}?page={params.page + 1}&per_page={params.per_page}"
                if params.page < total_pages else None
            ),
        )


MoviesPage = CustomizedPage[
    Page[T],
    UseFieldsAliases(
        results="movies"
    ),
]
