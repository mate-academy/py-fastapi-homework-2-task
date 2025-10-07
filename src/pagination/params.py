from typing import Annotated

from fastapi import Query
from fastapi_pagination.bases import AbstractParams, RawParams
from pydantic import BaseModel


class Params(BaseModel, AbstractParams):
    page: Annotated[int, Query(..., ge=1)] = 1
    per_page: Annotated[int, Query(..., ge=1, le=20)] = 10

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.per_page,
            offset=(self.page - 1) * self.per_page,
            include_total=True,
        )
