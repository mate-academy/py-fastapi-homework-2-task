from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud import get_movies, get_or_create, get_movie, delete_movie
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListSchema,
    MovieCreateSchema,
    MovieReadSchema,
    MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListSchema)
async def get_all_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    movies = await get_movies(db, per_page, page)
    count_result = await db.execute(
        select(func.count()).select_from(MovieModel)
    )
    count = count_result.scalar()
    page_count = (count + per_page - 1) // per_page

    prev_page = (
        None
        if page <= 1
        else f"/theater/movies/?page={page - 1}&per_page={per_page}"
    )
    next_page = (
        None
        if page >= page_count
        else f"/theater/movies/?page={page + 1}&per_page={per_page}"
    )

    return MovieListSchema.model_validate(
        {
            "movies": movies,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": page_count,
            "total_items": count,
        }
    )


@router.post("/movies/", response_model=MovieReadSchema, status_code=201)
async def create_movie(
    movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    if existing.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    genre_objs = [
        await get_or_create(GenreModel, db, name=name) for name in movie.genres
    ]
    actor_objs = [
        await get_or_create(ActorModel, db, name=name) for name in movie.actors
    ]
    language_objs = [
        await get_or_create(LanguageModel, db, name=name)
        for name in movie.languages
    ]
    country_obj = await get_or_create(
        CountryModel, db, code=movie.country, name=movie.country
    )

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country_obj.id,
        genres=genre_objs,
        actors=actor_objs,
        languages=language_objs,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    full_movie = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    full_movie_obj = full_movie.unique().scalar_one()
    return MovieReadSchema.model_validate(full_movie_obj)


@router.get("/movies/{movie_id}/", response_model=MovieReadSchema)
async def read_movie(
    movie_id: int, db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def remove_film(
    movie_id: int, db: AsyncSession = Depends(get_db)
):
    deleted_movie = await delete_movie(db, movie_id)
    if not deleted_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int = Path(..., ge=1),
    update_data: MovieUpdateSchema = Body(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_dict = update_data.model_dump(exclude_unset=True)

    try:
        for field, value in update_dict.items():
            setattr(db_movie, field, value)
        await db.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
