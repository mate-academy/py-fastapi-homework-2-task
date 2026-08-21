from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    MovieModel,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()

LOAD_RELATIONS = (
    selectinload(MovieModel.country),
    selectinload(MovieModel.genres),
    selectinload(MovieModel.actors),
    selectinload(MovieModel.languages),
)


async def get_or_create(db: AsyncSession, model, match_field: str, value: str):
    stmt = select(model).where(getattr(model, match_field) == value)
    obj = (await db.execute(stmt)).scalars().first()
    if obj is None:
        obj = model(**{match_field: value})
        db.add(obj)
        await db.flush()
    return obj


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = (await db.execute(select(func.count(MovieModel.id)))).scalar_one()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = (await db.execute(stmt)).scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name, MovieModel.date == movie_data.date
    )
    if (await db.execute(stmt)).scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )

    try:
        country = await get_or_create(db, CountryModel, "code", movie_data.country)
        genres = [
            await get_or_create(db, GenreModel, "name", n) for n in movie_data.genres
        ]
        actors = [
            await get_or_create(db, ActorModel, "name", n) for n in movie_data.actors
        ]
        languages = [
            await get_or_create(db, LanguageModel, "name", n)
            for n in movie_data.languages
        ]

        movie = MovieModel(
            **movie_data.model_dump(
                exclude={"country", "genres", "actors", "languages"}
            ),
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        db.add(movie)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    stmt = select(MovieModel).options(*LOAD_RELATIONS).where(MovieModel.id == movie.id)
    return (await db.execute(stmt)).scalars().first()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).options(*LOAD_RELATIONS).where(MovieModel.id == movie_id)
    movie = (await db.execute(stmt)).scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = (
        (await db.execute(select(MovieModel).where(MovieModel.id == movie_id)))
        .scalars()
        .first()
    )
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    movie = (
        (await db.execute(select(MovieModel).where(MovieModel.id == movie_id)))
        .scalars()
        .first()
    )
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    try:
        for field, value in movie_data.model_dump(exclude_unset=True).items():
            setattr(movie, field, value)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
