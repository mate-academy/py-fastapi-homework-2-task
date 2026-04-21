import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreate,
    MovieUpdate,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(ge=1, default=1),
    per_page: int = Query(ge=1, le=20, default=10),
):
    offset = (page - 1) * per_page
    limit = per_page
    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(limit)
    )
    movies = result.scalars().all()

    total = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total.scalar_one()

    if not movies or total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def get_or_create(model, db: AsyncSession, **kwargs):
    result = await db.execute(
        select(model).where(*(getattr(model, k) == v for k, v in kwargs.items()))
    )
    obj = result.scalar_one_or_none()
    if not obj:
        obj = model(**kwargs)
        db.add(obj)
        await db.flush()
    return obj


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie: MovieCreate,
    db: AsyncSession = Depends(get_db),
):
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )
    if existing_movie is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie.name}' "
                f"and release date '{movie.date}' already exists."
            ),
        )

    country = await get_or_create(CountryModel, db, code=movie.country)

    genres = []
    for genre_name in movie.genres:
        genre = await get_or_create(GenreModel, db, name=genre_name)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = await get_or_create(ActorModel, db, name=actor_name)
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = await get_or_create(LanguageModel, db, name=language_name)
        languages.append(language)

    movie = MovieModel(
        name=movie.name,
        date=movie.date,
        overview=movie.overview,
        status=movie.status,
        score=movie.score,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )
    movie = result.scalar_one()

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", response_model=dict)
async def update_movie(
    movie_id: int, movie_in: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_in.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
