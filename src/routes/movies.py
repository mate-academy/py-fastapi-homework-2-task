from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)


router = APIRouter()

MOVIE_DETAIL_OPTIONS = (
    joinedload(MovieModel.country),
    selectinload(MovieModel.genres),
    selectinload(MovieModel.actors),
    selectinload(MovieModel.languages),
)


async def get_movie_or_404(db: AsyncSession, movie_id: int, *options) -> MovieModel:
    movie = await db.get(MovieModel, movie_id, options=options)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


async def get_or_create(db: AsyncSession, model, **fields):
    instance = await db.scalar(select(model).filter_by(**fields))

    if instance is None:
        instance = model(**fields)
        db.add(instance)

    return instance


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    movies = await db.scalars(
        select(MovieModel)
        .order_by(*MovieModel.default_order_by())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    return MovieListResponseSchema(
        movies=movies.all(),
        prev_page=f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    duplicate_id = await db.scalar(
        select(MovieModel.id).where(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date)
    )

    if duplicate_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )

    try:
        movie = MovieModel(
            **movie_data.model_dump(exclude={"country", "genres", "actors", "languages"}),
            country=await get_or_create(db, CountryModel, code=movie_data.country),
            genres=[await get_or_create(db, GenreModel, name=name) for name in movie_data.genres],
            actors=[await get_or_create(db, ActorModel, name=name) for name in movie_data.actors],
            languages=[await get_or_create(db, LanguageModel, name=name) for name in movie_data.languages],
        )
        db.add(movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    return await get_movie_or_404(db, movie_id, *MOVIE_DETAIL_OPTIONS)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_or_404(db, movie_id)

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_or_404(db, movie_id)

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
