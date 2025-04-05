from math import ceil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import (
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


async def get_or_create_model(
    db: AsyncSession, model: type, name_field: str, names: List[str]
) -> List:
    if not names:
        return []

    items = []
    for name in names:
        result = await db.execute(
            select(model).where(getattr(model, name_field) == name)
        )
        item = result.scalar_one_or_none()
        if not item:
            item = model(**{name_field: name})
            db.add(item)
        items.append(item)
    return items


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    )

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = ceil(total_items / per_page)

    return {
        "movies": [MovieListItemSchema.model_validate(movie) for movie in movies],
        "prev_page": (
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        "next_page": (
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MovieDetailSchema)
async def create_movie(
    movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    existing_stmt = select(MovieModel).where(
        (MovieModel.name == movie_data.name),
        (MovieModel.date == movie_data.date)
    )
    existing_result = await db.execute(existing_stmt)
    existing_movie = existing_result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )

    movie = MovieModel(
        **movie_data.model_dump(exclude={"genres", "actors", "languages", "country"})
    )

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie_data.country.upper())
    )
    if not country:
        country = CountryModel(code=movie_data.country.upper())
        db.add(country)
        await db.flush()

    movie.country = country

    movie.genres = await get_or_create_model(db, GenreModel, "name", movie_data.genres)
    movie.actors = await get_or_create_model(db, ActorModel, "name", movie_data.actors)
    movie.languages = await get_or_create_model(
        db, LanguageModel, "name", movie_data.languages
    )

    db.add(movie)
    await db.flush()
    await db.commit()
    await db.refresh(movie, ["genres", "actors", "languages"])
    return movie


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie)
        return {"detail": "Movie updated successfully."}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid data")


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return None
