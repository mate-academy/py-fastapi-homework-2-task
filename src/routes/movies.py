from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import GenreModel, ActorModel, LanguageModel
from services.dependencies import get_movie_by_id
from services.helpers import get_or_create_related, get_or_create_country
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateRequestSchema,
    MovieDetailSchema, MovieUpdateRequestSchema,
)

router = APIRouter(
    prefix="/movies",
    tags=["movies"],
)


def get_pagination_links(
        total_pages: int | None = None,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    prev_page = None
    next_page = None

    if page > 1:
        prev_page = (
            f"/theater/movies/"
            f"?page={page - 1}&per_page={per_page}"
        )

    if page < total_pages:
        next_page = (
            f"/theater/movies/"
            f"?page={page + 1}&per_page={per_page}"
        )
    return prev_page, next_page


@router.get(
    "/",
    response_model=MovieListResponseSchema
)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    offset = (page - 1) * per_page

    query = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )
    count_query = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_query)
    total_items = count_result.scalar_one_or_none()
    total_pages = (total_items + per_page -1) // per_page

    prev_page, next_page = get_pagination_links(
        total_pages=total_pages,
        page=page,
        per_page=per_page
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=201,
)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MovieModel:
    country = await get_or_create_country(
        db, movie_data.country
    )
    genres = [
        await get_or_create_related(db, GenreModel, genre)
        for genre in movie_data.genres
    ]
    actors = [
        await get_or_create_related(db, ActorModel, actor)
        for actor in movie_data.actors
    ]
    languages = [
        await get_or_create_related(db, LanguageModel, language)
        for language in movie_data.languages
    ]

    movie_data_dict = movie_data.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )

    movie = MovieModel(
        **movie_data_dict,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )

    movie = result.unique().scalar_one()

    return movie


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie(
    movie: MovieModel = Depends(get_movie_by_id),
) -> MovieModel:
    return movie


@router.delete(
    "/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie: MovieModel = Depends(get_movie_by_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.delete(movie)
    await db.commit()


@router.patch(
    "/{movie_id}/",
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_data: MovieUpdateRequestSchema,
    movie: MovieModel = Depends(get_movie_by_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
