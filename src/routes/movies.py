import math
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)
from database import get_db, models

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(func.count(models.MovieModel.id)))
    total_items = result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page

    result = await db.execute(
        select(models.MovieModel)
        .order_by(models.MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"{base_url}?page={page+1}&per_page={per_page}" if page < total_pages else None
    )

    movie_items = [
        MovieListItemSchema(
            id=m.id, name=m.name, date=str(m.date), score=m.score, overview=m.overview
        )
        for m in movies
    ]

    return MovieListResponseSchema(
        movies=movie_items,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.MovieModel)
        .options(
            joinedload(models.MovieModel.country),
            joinedload(models.MovieModel.genres),
            joinedload(models.MovieModel.actors),
            joinedload(models.MovieModel.languages),
        )
        .where(models.MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.from_orm(movie)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # Проверка на дубликат
    result = await db.execute(
        select(models.MovieModel).where(
            models.MovieModel.name == movie.name, models.MovieModel.date == movie.date
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    result = await db.execute(
        select(models.CountryModel).where(models.CountryModel.code == movie.country)
    )
    country = result.scalars().first()
    if not country:
        country = models.CountryModel(code=movie.country, name=None)
        db.add(country)
        await db.flush()

    genres = []
    for g in movie.genres:
        result = await db.execute(
            select(models.GenreModel).where(models.GenreModel.name == g)
        )
        genre = result.scalars().first()
        if not genre:
            genre = models.GenreModel(name=g)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for a in movie.actors:
        result = await db.execute(
            select(models.ActorModel).where(models.ActorModel.name == a)
        )
        actor = result.scalars().first()
        if not actor:
            actor = models.ActorModel(name=a)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for l in movie.languages:
        result = await db.execute(
            select(models.LanguageModel).where(models.LanguageModel.name == l)
        )
        language = result.scalars().first()
        if not language:
            language = models.LanguageModel(name=l)
            db.add(language)
            await db.flush()
        languages.append(language)

    new_movie = models.MovieModel(
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

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(models.MovieModel)
        .options(
            joinedload(models.MovieModel.country),
            joinedload(models.MovieModel.genres),
            joinedload(models.MovieModel.actors),
            joinedload(models.MovieModel.languages),
        )
        .where(models.MovieModel.id == new_movie.id)
    )
    movie_with_relations = result.scalars().first()

    return MovieDetailSchema.from_orm(movie_with_relations)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.MovieModel).where(models.MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return None


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_id: int,
    movie_update: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.MovieModel).where(models.MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_movie = movie_update.dict(exclude_unset=True)

    for field, value in update_movie.items():
        setattr(movie, field, value)

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
