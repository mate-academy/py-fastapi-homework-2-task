import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import schemas
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from services.movie_service import validate_movie_business_rules

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieList)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = int(total_items_result.scalar_one())

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    movies_result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = list(movies_result.scalars().all())

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

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


@router.post("/movies/", response_model=schemas.MovieCreateResponse, status_code=201)
async def create_movie(
    payload: schemas.MovieCreateRequest, db: AsyncSession = Depends(get_db)
):

    dup_result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == payload.name, MovieModel.date == payload.date
        )
    )
    if dup_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Movie with name '{payload.name}' and release date '{payload.date}' already exists.",
        )

    validate_movie_business_rules(payload.model_dump(), movie=None)

    country_result = await db.execute(
        select(CountryModel).where(CountryModel.code == payload.country)
    )
    country = country_result.scalar_one_or_none()
    if country is None:
        country = CountryModel(code=payload.country, name=None)
        db.add(country)
        await db.flush()

    async def get_or_create_by_name(model_cls, name: str):
        r = await db.execute(select(model_cls).where(model_cls.name == name))
        obj = r.scalar_one_or_none()
        if obj is None:
            obj = model_cls(name=name)
            db.add(obj)
            await db.flush()
        return obj

    movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country_id=country.id,
    )

    movie.genres = [await get_or_create_by_name(GenreModel, n) for n in payload.genres]
    movie.actors = [await get_or_create_by_name(ActorModel, n) for n in payload.actors]
    movie.languages = [
        await get_or_create_by_name(LanguageModel, n) for n in payload.languages
    ]

    db.add(movie)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Movie already exists.")

    loaded_result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )
    return loaded_result.unique().scalar_one()


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetail)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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
    movie = result.unique().scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return Response(status_code=204)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int, movie_data: schemas.MovieUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    validate_movie_business_rules(update_data, movie)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
