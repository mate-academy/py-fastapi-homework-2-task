import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
)

router = APIRouter()

NOT_FOUND_MSG = "Movie with the given ID was not found."


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if not total_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )
    total_pages = math.ceil(total_items / per_page) if total_items else 0
    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    movies = (
        await db.scalars(
            select(MovieModel)
            .order_by(MovieModel.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page),
        )
    ).all()

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def _get_movie_with_relations(db: AsyncSession, movie_id: int):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    return (await db.execute(stmt)).scalars().first()


async def _get_or_create_by_name(db: AsyncSession, model, name: str):
    obj = (await db.execute(select(model).where(model.name == name))).scalars().first()
    if obj is None:
        obj = model(name=name)
        db.add(obj)
        await db.flush()
    return obj


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    duplicate = (
        await db.scalars(
            select(MovieModel).where(
                MovieModel.name == movie.name,
                MovieModel.date == movie.date,
            ),
        )
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie.name}' and release date "
                f"'{movie.date}' already exists."
            ),
        )

    country = (
        await db.scalars(select(CountryModel).where(CountryModel.code == movie.country))
    ).first()
    if country is None:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()
    genres = [await _get_or_create_by_name(db, GenreModel, n) for n in movie.genres]
    actors = [await _get_or_create_by_name(db, ActorModel, n) for n in movie.actors]
    languages = [
        await _get_or_create_by_name(db, LanguageModel, n) for n in movie.languages
    ]
    db_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(db_movie)
    await db.commit()

    return await _get_movie_with_relations(db, db_movie.id)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    film = await _get_movie_with_relations(db, movie_id)
    if film is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_MSG,
        )
    return film


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    film = await db.get(MovieModel, movie_id)
    if film is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_MSG,
        )
    await db.delete(film)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie: MovieUpdateSchema, movie_id: int, db: AsyncSession = Depends(get_db)
):
    film = await db.get(MovieModel, movie_id)
    if film is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_MSG,
        )
    for field, value in movie.model_dump(exclude_unset=True).items():
        setattr(film, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    return {"detail": "Movie updated successfully."}
