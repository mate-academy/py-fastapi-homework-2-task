from datetime import datetime, timedelta
import select
from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import MovieModel as Movie
from schemas.movies import MovieCreate, MovieUpdate


def get_movie(movie_id: int, db: AsyncSession):
    res = db.execute(select(Movie).where(Movie.id == movie_id))
    movie = res.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


def get_movies(db: AsyncSession):
    res = db.execute(select(Movie))
    movies = res.scalars().all()
    return movies


async def create_movie(db: AsyncSession, movie: MovieCreate):
    today = datetime.today().date()
    if movie.date < today:
        raise HTTPException(status_code=400, detail="Date is in the past.")
    if movie.date > today + timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail="Date must not be more than one year in the future.",
        )

    if not (0 <= movie.score <= 100):
        raise HTTPException(
            status_code=400, detail="Score must be between 0 and 100."
        )

    if movie.budget < 0:
        raise HTTPException(
            status_code=400, detail="Budget must be non-negative."
        )
    if movie.revenue < 0:
        raise HTTPException(
            status_code=400, detail="Revenue must be non-negative."
        )

    db_movie = Movie(**movie.dict())
    db.add(db_movie)
    await db.commit()
    await db.refresh(db_movie)
    return db_movie


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    res = await db.execute(select(Movie).where(Movie.id == movie_id))
    db_movie = res.scalar_one_or_none()

    if db_movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    if movie.name is not None:
        if len(movie.name) > 255:
            raise HTTPException(
                status_code=400, detail="Movie name exceeds 255 characters."
            )
        db_movie.name = movie.name

    if movie.date is not None:
        today = datetime.today().date()
        if movie.date < today:
            raise HTTPException(status_code=400, detail="Date is in the past.")
        if movie.date > today + timedelta(days=365):
            raise HTTPException(
                status_code=400,
                detail="Date must not be more than one year in the future.",
            )
        db_movie.date = movie.date

    if movie.score is not None:
        if not (0 <= movie.score <= 100):
            raise HTTPException(
                status_code=400, detail="Score must be between 0 and 100."
            )
        db_movie.score = movie.score

    if movie.overview is not None:
        db_movie.overview = movie.overview

    if movie.status is not None:
        db_movie.status = movie.status

    if movie.budget is not None:
        if movie.budget < 0:
            raise HTTPException(
                status_code=400, detail="Budget must be non-negative."
            )
        db_movie.budget = movie.budget

    if movie.revenue is not None:
        if movie.revenue < 0:
            raise HTTPException(
                status_code=400, detail="Revenue must be non-negative."
            )
        db_movie.revenue = movie.revenue

    if movie.country is not None:
        db_movie.country = movie.country

    if movie.genres is not None:
        db_movie.genres = movie.genres

    if movie.actors is not None:
        db_movie.actors = movie.actors

    if movie.languages is not None:
        db_movie.languages = movie.languages

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


def delete_movie(db: AsyncSession, movie_id: int):
    res = db.execute(select(Movie).where(Movie.id == movie_id))
    movie = res.scalar_one_or_none()
    if movie is None:
        return None
    db.delete(movie)
    db.commit()
    return Response(status_code=204)
