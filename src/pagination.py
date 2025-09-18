from fastapi_pagination import Page, Params
from pydantic import Field


class CustomParams(Params):
    page: int = Field(1, ge=1, le=20)
    per_page: int = Field(10, ge=1, le=20)
