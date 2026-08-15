from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import timedelta, date as Date
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieUpdate,
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreate,
)

router = APIRouter()


async def get_or_create(db: AsyncSession, model, field: str, value: str):
    result = await db.execute(select(model).where(getattr(model, field) == value))
    instance = result.scalar_one_or_none()

    if instance is not None:
        return instance

    instance = model(**{field: value})

    db.add(instance)
    await db.flush()

    return instance


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
)
async def get_all_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    stmt = select(func.count(MovieModel.id))
    items = await db.execute(stmt)
    total_items = items.scalar()
    total_pages = (total_items + per_page - 1) // per_page

    stmt = (
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(desc(MovieModel.id))
    )
    movies = await db.execute(stmt)
    movies = movies.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=(
            (f"/theater/movies/?page={page - 1}&per_page={per_page}")
            if page > 1
            else None
        ),
        next_page=(
            (f"/theater/movies/?page={page + 1}&per_page={per_page}")
            if page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_movie(
    movie: MovieCreate,
    db: AsyncSession = Depends(get_db),
):
    if (
        len(movie.name) > 255
        or movie.date > Date.today() + timedelta(days=365)
        or not 0 <= movie.score <= 100
        or movie.budget < 0
        or movie.revenue < 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    stmt = select(MovieModel).where(
        MovieModel.name == movie.name, MovieModel.date == movie.date
    )
    movie_exists = await db.execute(stmt)

    if movie_exists.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country = await get_or_create(
        db=db,
        model=CountryModel,
        field="code",
        value=movie.country,
    )

    genres = []
    for genre in movie.genres:
        genres.append(
            await get_or_create(
                db=db,
                model=GenreModel,
                field="name",
                value=genre,
            )
        )

    actors = []
    for actor in movie.actors:
        actors.append(
            await get_or_create(
                db=db,
                model=ActorModel,
                field="name",
                value=actor,
            )
        )

    languages = []
    for language in movie.languages:
        languages.append(
            await get_or_create(
                db=db,
                model=LanguageModel,
                field="name",
                value=language,
            )
        )

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

    stmt = (
        select(MovieModel)
        .where(MovieModel.id == db_movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def read_single_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    db_movie = await db.scalar(stmt)

    if db_movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return db_movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    db_movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))

    if db_movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(db_movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    if movie.name is not None and len(movie.name) > 255:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    if movie.date is not None and movie.date > Date.today() + timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    if movie.score is not None and not 0 <= movie.score <= 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    if movie.budget is not None and movie.budget < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    if movie.revenue is not None and movie.revenue < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    db_movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))

    if db_movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    movie_data = movie.model_dump(
        exclude_unset=True, exclude={"country", "genres", "actors", "languages"}
    )

    for field, value in movie_data.items():
        setattr(db_movie, field, value)

    if movie.country is not None:
        db_movie.country = await get_or_create(
            db=db,
            model=CountryModel,
            field="code",
            value=movie.country,
        )
    if movie.genres is not None:
        db_movie.genres = [
            await get_or_create(
                db=db,
                model=GenreModel,
                field="name",
                value=genre,
            )
            for genre in movie.genres
        ]
    if movie.actors is not None:
        db_movie.actors = [
            await get_or_create(
                db=db,
                model=ActorModel,
                field="name",
                value=actor,
            )
            for actor in movie.actors
        ]
    if movie.languages is not None:
        db_movie.languages = [
            await get_or_create(
                db=db,
                model=LanguageModel,
                field="name",
                value=language,
            )
            for language in movie.languages
        ]

    await db.commit()

    return {"detail": "Movie updated successfully."}
