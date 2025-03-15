from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieStatusEnum
from schemas import MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100)
):
    offset = (page - 1) * per_page

    count_query = select(func.count(MovieModel.id))
    result = await db.execute(count_query)
    total_items = result.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page)

    query = select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    result = await db.execute(query)
    movies = [
        MovieListItemSchema.model_validate(
            {k: v for k, v in mov.__dict__.items() if not k.startswith('_')}
        )
        for mov in result.scalars().all()
    ]

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page_url = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page_url = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=list(movies),
        prev_page=prev_page_url,
        next_page=next_page_url,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    # query = (select(MovieModel)
    #          .where(MovieModel.id == movie_id)
    #          .options(selectinload(MovieModel.country)))
    # result = await db.execute(query)
    # movie = result.scalar_one_or_none()
    #
    # if movie is None:
    #     raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    #
    # return MovieDetailSchema(**movie)
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    if isinstance(movie.status, str):
        try:
            movie.status = MovieStatusEnum(movie.status)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid status value in the database.")

        return MovieDetailSchema.model_validate(movie, from_attributes=True)
