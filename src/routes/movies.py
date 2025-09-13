from datetime import timedelta, date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieModel
from src.schemas.movies import (MovieListResponseSchema,
                                MovieCreateSchema,
                                MovieOut,
                                MovieUpdateSchema,
                                MovieListItemSchema,
                                MovieDetailSchema
                                )

router = APIRouter()


async def get_or_create_country(db: AsyncSession, code: str) -> CountryModel:
    code = code.upper()
    result = await db.execute(select(CountryModel).where(CountryModel.code == code))
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=code, name=None)
        db.add(country)
        await db.flush()
    return country


async def get_or_create_by_name(db: AsyncSession, model, name: str):
    result = await db.execute(select(model).where(model.name == name))
    obj = result.scalar_one_or_none()
    if not obj:
        obj = model(name=name)
        db.add(obj)
        await db.flush()
    return obj


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    total_items = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().unique().all()

    movies_items = [
        MovieListItemSchema(
            id=m.id,
            name=m.name,
            date=m.date,
            score=m.score,
            overview=m.overview
        )
        for m in movies
    ]

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies_items,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieOut, status_code=201)
async def create_movie(movie_in: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    if movie_in.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if not (0 <= movie_in.score <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie_in.budget < 0 or movie_in.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    query = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date,
    )
    result = await db.execute(query)
    existing_movie = result.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists."
        )

    country = await get_or_create_country(db, movie_in.country)
    genres = [await get_or_create_by_name(db, GenreModel, g) for g in movie_in.genres]
    actors = [await get_or_create_by_name(db, ActorModel, a) for a in movie_in.actors]
    languages = [await get_or_create_by_name(db, LanguageModel, lang) for lang in movie_in.languages]

    movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=float(movie_in.budget),
        revenue=float(movie_in.revenue),
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

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

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieOut)
async def get_movie(
        movie_id: int = Path(..., ge=1),
        db: AsyncSession = Depends(get_db)
):
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
    movie = result.scalars().unique().one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()

    return Response(status_code=204)


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_in: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie_in.name is not None:
        movie.name = movie_in.name

    if movie_in.date is not None:
        if movie_in.date > date.today() + timedelta(days=365):
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.date = movie_in.date

    if movie_in.score is not None:
        if not (0 <= movie_in.score <= 100):
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.score = movie_in.score

    if movie_in.overview is not None:
        movie.overview = movie_in.overview

    if movie_in.status is not None:
        movie.status = movie_in.status

    if movie_in.budget is not None:
        if movie_in.budget < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.budget = float(movie_in.budget)

    if movie_in.revenue is not None:
        if movie_in.revenue < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.revenue = float(movie_in.revenue)

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
