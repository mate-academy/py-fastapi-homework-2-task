from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()


async def get_or_create(session, model, **kwargs):
    result = await session.execute(
        select(model).filter_by(**kwargs)
    )
    instance = result.scalar_one_or_none()

    if instance is None:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()

    return instance


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=201,
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    country = await get_or_create(
        db,
        CountryModel,
        code=movie_data.country,
    )
    genres = []

    for genre_name in movie_data.genres:
        genre = await get_or_create(
            db,
            GenreModel,
            name=genre_name,
        )
        genres.append(genre)

    actors = []

    for actor_name in movie_data.actors:
        actor = await get_or_create(
            db,
            ActorModel,
            name=actor_name,
        )
        actors.append(actor)

    languages = []

    for language_name in movie_data.languages:
        language = await get_or_create(
            db,
            LanguageModel,
            name=language_name,
        )
        languages.append(language)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    try:
        db.add(movie)
        await db.commit()
        await db.refresh(movie)

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

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    return movie


@router.get(
    "/",
    response_model=MovieListResponseSchema,
)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count_query = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_query)
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="Page not found."
        )

    offset = (page - 1) * per_page

    movies_query = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    movies_result = await db.execute(movies_query)

    movies = movies_result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )

    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        total_pages=total_pages,
        total_items=total_items,
        prev_page=prev_page,
        next_page=next_page,
    )


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie_query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    result = await db.execute(movie_query)
    movie = result.unique().scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete(
    "/{movie_id}/",
    status_code=204,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch(
    "/{movie_id}/",
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
