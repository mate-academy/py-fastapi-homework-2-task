import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas import (MovieCreateSchema, MovieDetailResponseSchema,
                     MovieListResponseSchema, MovieUpdateSchema)

router = APIRouter()


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_info: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie_exists = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_info.name, MovieModel.date == movie_info.date
        )
    )

    if movie_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_info.name}' "
            f"and release date '{movie_info.date}' already exists.",
        )

    try:
        country = await db.scalar(
            select(CountryModel).where(CountryModel.code == movie_info.country)
        )

        if not country:
            country = CountryModel(
                code=movie_info.country,
                name=None,
            )
            db.add(country)
            await db.flush()

        genres = []
        for genre_input in movie_info.genres:
            genre_obj = await db.scalar(
                select(GenreModel).where(GenreModel.name == genre_input)
            )
            if not genre_obj:
                genre_obj = GenreModel(name=genre_input)
                db.add(genre_obj)
                await db.flush()
            genres.append(genre_obj)

        actors = []
        for actor_input in movie_info.actors:
            actor_obj = await db.scalar(
                select(ActorModel).where(ActorModel.name == actor_input)
            )
            if not actor_obj:
                actor_obj = ActorModel(name=actor_input)
                db.add(actor_obj)
                await db.flush()
            actors.append(actor_obj)

        languages = []
        for language_input in movie_info.languages:
            language_obj = await db.scalar(
                select(LanguageModel).where(LanguageModel.name == language_input)
            )
            if not language_obj:
                language_obj = LanguageModel(name=language_input)
                db.add(language_obj)
                await db.flush()
            languages.append(language_obj)

        new_movie = MovieModel(
            name=movie_info.name,
            date=movie_info.date,
            score=movie_info.score,
            overview=movie_info.overview,
            status=movie_info.status,
            budget=movie_info.budget,
            revenue=movie_info.revenue,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )

        db.add(new_movie)
        await db.flush()
        await db.commit()

        return new_movie

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data."
        )


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
) -> MovieListResponseSchema:
    total_items = int(await db.scalar(select(func.count()).select_from(MovieModel)))
    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    offset = (page - 1) * per_page
    res = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = res.scalars().all()

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.patch(
    "/movies/{movie_id}/",
)
async def patch_movie(
    movie_id: int, movie_update: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        db.add(movie)
        await db.commit()
        return {"detail": "Movie updated successfully."}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data."
        )


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()
