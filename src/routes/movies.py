import math
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieDetailSchema,
    MovieListResponseSchema
)

router = APIRouter()


async def get_or_create(session, model, field, value, **kwargs):
    stmt = select(model).filter(getattr(model, field) == value)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    if not instance:
        instance = model(**{field: value}, **kwargs)
        session.add(instance)
        await session.flush()
    return instance


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items_stmt = select(func.count(MovieModel.id))
    total_items = (await db.execute(total_items_stmt)).scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    base_url = "/theater/movies/"
    prev_p = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_p = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "total_pages": total_pages,
        "total_items": total_items,
        "prev_page": prev_p,
        "next_page": next_p
    }


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    exists_stmt = select(MovieModel).filter_by(
        name=movie_data.name,
        date=movie_data.date
    )
    if (await db.execute(exists_stmt)).scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' and "
                f"release date '{movie_data.date}' already exists."
            )
        )

    try:
        country = await get_or_create(db, CountryModel, "code", movie_data.country)
        genres = [await get_or_create(db, GenreModel, "name", g) for g in movie_data.genres]
        actors = [await get_or_create(db, ActorModel, "name", a) for a in movie_data.actors]
        langs = [await get_or_create(db, LanguageModel, "name", lang) for lang in movie_data.languages]

        new_movie = MovieModel(
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
            languages=langs
        )
        db.add(new_movie)
        await db.commit()

        stmt = select(MovieModel).options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        ).filter(MovieModel.id == new_movie.id)
        result = await db.execute(stmt)
        return result.unique().scalar_one()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).filter(MovieModel.id == movie_id)

    result = await db.execute(stmt)
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.patch("/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).filter(MovieModel.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_dict = movie_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(movie, key, value)

    try:
        await db.commit()
        return {"detail": "Movie updated successfully."}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).filter(MovieModel.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return Response(status_code=204)
