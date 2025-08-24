from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import MovieModel


async def get_movie_by_id(session: AsyncSession, movie_id: int) -> MovieModel:
    """Fetch a single movie with related entities"""
    result = await session.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


ALLOWED_STATUSES = {"Released", "Post Production", "In Production"}


async def update_movie_partial(db: AsyncSession, movie_id: int, update_data: dict):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    for field, value in update_data.items():

        if value is None:
            continue

        if field == "score":
            if not (0 <= value <= 100):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="score must be between 0 and 100"
                )

        elif field in ("budget", "revenue"):
            if value < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field} must be greater than or equal to 0"
                )

        elif field == "name":
            if len(value) > 255:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="name must be at most 255 characters"
                )

        elif field == "date":
            if value > date.today() + timedelta(days=365):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="date cannot be more than one year in the future"
                )

        elif field == "status":
            if value not in ALLOWED_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"status must be one of {ALLOWED_STATUSES}"
                )
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )

    return movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
