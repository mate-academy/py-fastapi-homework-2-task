from pydantic import BaseModel


class BaseListPaginationSchema(BaseModel):
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int
