import math

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import service
from database import get_db, MovieModel

from schemas import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreate,
    MovieUpdate
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page

    movies = await db.scalars(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .offset(offset)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )

    movies = movies.all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = None
    next_page = None
    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )
    total_pages = math.ceil(total_items / per_page)

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        movie: MovieCreate,
        db: AsyncSession = Depends(get_db)
):
    db_movie = await service.check_for_movie_in_database(movie=movie, db=db)
    if db_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release"
                   f" date '{movie.date}' already exists."
        )

    await service.check_for_date(movie.date)
    await service.check_for_name_len(movie.name)

    country = await service.check_for_country_in_database(code=movie.country, db=db)
    genres = []
    actors = []
    languages = []

    for genre in movie.genres:
        temp_genre = await service.check_for_genre_in_database(genre=genre, db=db)
        if temp_genre:
            genres.append(temp_genre)
        else:
            genre = await service.create_genre(genre=genre, db=db)
            genres.append(genre)

    for actor in movie.actors:
        temp_actor = await service.check_for_actor_in_database(actor=actor, db=db)
        if temp_actor:
            actors.append(temp_actor)
        else:
            actor = await service.create_actor(name=actor, db=db)
            actors.append(actor)

    for language in movie.languages:
        temp_language = await service.check_for_language_in_database(
            language=language, db=db
        )
        if temp_language:
            languages.append(temp_language)
        else:
            language = await service.create_language(name=language, db=db)
            languages.append(language)

    if not country:
        country = await service.create_country(code=movie.country, db=db)

    db_movie = MovieModel(
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
    db.add(db_movie)
    await db.commit()
    db_movie = await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == db_movie.id)
    )

    return db_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
    )

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie: MovieUpdate,
        db: AsyncSession = Depends(get_db),
):
    if movie.date:
        await service.check_for_date(movie.date)
    if movie.name:
        await service.check_for_name_len(movie.name)
    db_movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
