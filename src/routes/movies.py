from contextvars import ContextVar
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, Select, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieListItemSchema

router = APIRouter()

request_object: ContextVar[Request] = ContextVar("request")


class PaginationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_object.set(request)
        response = await call_next(request)
        return response


class Paginator:
    def __init__(self, session: AsyncSession, query: Select, page: int, per_page: int):
        self.session = session
        self.query = query
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page
        self.request = request_object.get()
        self.number_of_pages = 0
        self.next_page = ""
        self.previous_page = ""

    def _get_next_page(self) -> Optional[str]:
        if self.page >= self.number_of_pages:
            return None
        url = self.request.url.include_query_params(page=self.page + 1)
        return str(url)

    def _get_previous_page(self) -> Optional[str]:
        if self.page == 1:
            return None
        url = self.request.url.include_query_params(page=self.page - 1)
        return str(url)

    async def get_response(self) -> dict:
        return {
            "total_items": await self._get_total_count(),
            "total_pages": self.number_of_pages,
            "prev_page": self._get_previous_page(),
            "next_page": self._get_next_page(),
            "movies": [
                movie
                for movie in await self.session.scalars(
                    self.query.limit(self.per_page).offset(self.offset)
                )
            ],
        }

    def _get_number_of_pages(self, count: int) -> int:
        rest = count % self.per_page
        quotient = count // self.per_page
        return quotient if not rest else quotient + 1

    async def _get_total_count(self) -> int:
        count = await self.session.scalar(
            select(func.count()).select_from(self.query.subquery())
        )
        self.number_of_pages = self._get_number_of_pages(count)
        return count


async def paginate(
    session: AsyncSession, query: Select, page: int, per_page: int
) -> dict:
    paginator = Paginator(session, query, page, per_page)
    result = await paginator.get_response()

    if result["total_items"] == 0 or paginator.number_of_pages < page:
        raise HTTPException(status_code=404, detail="No movies found.")
    return result


@router.get("/movies/", response_model=MovieListResponseSchema[MovieListItemSchema])
async def get_films(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await paginate(
        db, select(MovieModel).order_by(desc(MovieModel.id)), page, per_page
    )
