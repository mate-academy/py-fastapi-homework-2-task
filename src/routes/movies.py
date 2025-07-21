from contextvars import ContextVar
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, Select, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, Base
from schemas import MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema
from schemas.movies import MovieCreateSchema, MovieUpdateSchema

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


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


async def items_get_or_create(
    item_names: list[str], model: type[Base], session: AsyncSession
) -> list:
    items = []
    for name in item_names:
        query = await session.execute(select(model).where(model.name == name))
        item = query.scalar_one_or_none()
        if not item:
            item = model(name=name)
            session.add(item)
            await session.commit()
            await session.refresh(item)
        items.append(item)
    return items


@router.post("/movies/", response_model=MovieDetailSchema)
async def post_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    movie_data = movie.model_dump()
    country_code = movie_data.pop("country")
    country_query = await db.execute(
        select(CountryModel).where(CountryModel.code == country_code)
    )
    country = country_query.scalar_one_or_none()
    if not country:
        country = CountryModel(code=country_code)

    genres = await items_get_or_create(movie_data.pop("genres"), GenreModel, db)
    actors = await items_get_or_create(movie_data.pop("actors"), ActorModel, db)
    languages = await items_get_or_create(
        movie_data.pop("languages"), LanguageModel, db
    )

    created_movie = MovieModel(
        country=country, genres=genres, actors=actors, languages=languages, **movie_data
    )
    db.add(created_movie)

    try:
        await db.commit()
        await db.refresh(created_movie)
        result = await db.execute(
            select(MovieModel)
            .where(MovieModel.id == created_movie.id)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
        )
        new_movie = result.scalar()
        return new_movie
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="Movie with the given name and date already exists."
        )
    except Exception as exc:
        await db.rollback()
        raise exc


@router.patch("/movies/{movie_id}/")
async def patch_movie(
    movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_update = result.scalar_one_or_none()
    if not movie_to_update:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie_to_update, key, value)
    await db.commit()
    await db.refresh(movie_to_update)
    return {"detail": "Movie updated successfully."}
