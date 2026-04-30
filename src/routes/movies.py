from datetime import timedelta, date
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieModel
)
from schemas import MovieListResponseSchema, MovieDetailResponseSchema, MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> MovieDetailResponseSchema:
    if not (0 <= movie.score <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    if existing_movie.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = await db.execute(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    country = country.scalar()

    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in movie.genres or []:
        result = await db.execute(
            select(GenreModel).where(GenreModel.name == name)
        )
        result = result.scalar()

        if not result:
            result = GenreModel(name=name)
            db.add(result)
            await db.flush()
        genres.append(result)

    actors = []
    for name in movie.actors or []:
        result = await db.execute(
            select(ActorModel).where(ActorModel.name == name)
        )
        result = result.scalar()

        if not result:
            result = ActorModel(name=name)
            db.add(result)
            await db.flush()
        actors.append(result)

    languages = []
    for name in movie.languages or []:
        result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        result = result.scalar()

        if not result:
            result = LanguageModel(name=name)
            db.add(result)
            await db.flush()
        languages.append(result)

    movie_create = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
    )

    movie_create.genres = genres
    movie_create.actors = actors
    movie_create.languages = languages

    db.add(movie_create)
    await db.commit()
    await db.refresh(movie_create)

    result = await db.execute(
        select(MovieModel).options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        ).where(MovieModel.id == movie_create.id)
    )

    movie_with_relations = result.scalar_one()

    return movie_with_relations


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailResponseSchema:
    result = await db.execute(
        select(MovieModel).options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        ).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return None


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie.model_dump(exclude_unset=True)

    if "score" in update_data and not (0 <= update_data["score"] <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "budget" in update_data and update_data["budget"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "revenue" in update_data and update_data["revenue"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "date" in update_data and update_data["date"] > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)

    return {"detail": "Movie updated successfully."}
