import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from schemas.movies import (
    MovieCreateRequest,
    MovieUpdateRequest,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieListItemSchema,
)
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()


@router.get("/movies/")
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    total = await db.execute(select(func.count(MovieModel.id)))
    total_items = total.scalar()

    if page == 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if offset + per_page < total_items else None

    movies = await db.execute(select(MovieModel).offset(offset).limit(per_page).order_by(MovieModel.id.desc()))
    movie_list = movies.scalars().all()

    if not movie_list:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movie_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=math.ceil(total_items / per_page),
        total_items=total_items
    )


@router.post("/movies/", status_code=201)
async def create_movie(movie: MovieCreateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in movie.genres:
        result = await db.execute(select(GenreModel).where(GenreModel.name == name))
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in movie.actors:
        result = await db.execute(select(ActorModel).where(ActorModel.name == name))
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for name in movie.languages:
        result = await db.execute(select(LanguageModel).where(LanguageModel.name == name))
        language = result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    new_movie = MovieModel(
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

    try:
        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie)
        return new_movie
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )


@router.get("/movies/{movie_id}/")
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id).options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
    )
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie: MovieUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    existing_movie = result.scalar_one_or_none()

    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for key, value in movie.model_dump(exclude_unset=True).items():
        setattr(existing_movie, key, value)

    try:
        await db.commit()
        await db.refresh(existing_movie)
        return {"detail": "Movie updated successfully."}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/movies/{movie_id}/")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    existing_movie = result.scalar_one_or_none()

    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    try:
        await db.delete(existing_movie)
        await db.commit()
        return Response(status_code=204)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error occurred while deleting the movie.")
