import math
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import (
    MovieListItemSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieCreate,
    PaginationResponseSchema,
    MovieUpdate
)

router = APIRouter()


@router.get("/movies/", response_model=PaginationResponseSchema)
async def get_movies(
    per_page: int = Query(default=10, ge=1, le=20),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    result = await db.execute(select(MovieModel).offset(offset).limit(per_page).order_by(MovieModel.id.desc()))

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_result.scalar()

    total_pages = math.ceil(total_items / per_page)

    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if offset + len(movies) < total_items else None
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None

    response = {
        "movies": movies,
        "next_page": next_page,
        "prev_page": prev_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }

    return response


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
        joinedload(MovieModel.country)))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/movies/", response_model=MovieListResponseSchema, status_code=201)
async def create_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    existing_movie = result.scalars().first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    if (
        len(movie.name) > 255
        or not (0 <= movie.score <= 100)
        or movie.budget < 0
        or movie.revenue < 0
        or movie.date > date.today() + timedelta(days=365)
    ):
        raise HTTPException(
            status_code=400,
            detail="The input data is invalid (e.g., missing required fields, invalid values)"
        )

    result_genres = await db.execute(select(GenreModel).where(GenreModel.name.in_(movie.genres)))
    genres = result_genres.scalars().all()

    result_actors = await db.execute(select(ActorModel).where(ActorModel.name.in_(movie.actors)))
    actors = result_actors.scalars().all()

    result_languages = await db.execute(select(LanguageModel).where(LanguageModel.name.in_(movie.languages)))
    languages = result_languages.scalars().all()

    result_country = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = result_country.scalars().first()

    new_genres = []
    existing_genre_names = {g.name for g in genres}
    for g_name in movie.genres:
        if g_name not in existing_genre_names:
            new_g = GenreModel(name=g_name)
            db.add(new_g)
            new_genres.append(new_g)

    await db.flush()

    genres += new_genres

    new_actors = []
    existing_actor_names = {a.name for a in actors}
    for a_name in movie.actors:
        if a_name not in existing_actor_names:
            new_a = ActorModel(name=a_name)
            db.add(new_a)
            new_actors.append(new_a)

    await db.flush()
    actors += new_actors

    new_languages = []
    existing_language_names = {language.name for language in languages}
    for l_name in movie.languages:
        if l_name not in existing_language_names:
            new_l = LanguageModel(name=l_name)
            db.add(new_l)
            new_languages.append(new_l)

    await db.flush()
    languages += new_languages

    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)

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

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
            joinedload(MovieModel.country),
        )
        .where(MovieModel.id == new_movie.id)
    )
    movie_with_relations = result.scalars().first()

    return movie_with_relations


@router.patch("/movies/{movie_id}/")
async def patch_movie(movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)):
    get_movie = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_db = get_movie.scalars().first()
    if movie.score is not None:
        if not (0 <= movie.score <= 100):
            raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie.budget is not None and movie.budget < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie.revenue is not None and movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie.name is not None:
        movie_db.name = movie.name
    if movie.score is not None:
        movie_db.score = movie.score
    if movie.overview is not None:
        movie_db.overview = movie.overview
    if movie.status is not None:
        movie_db.status = movie.status
    if movie.budget is not None:
        movie_db.budget = movie.budget
    if movie.revenue is not None:
        movie_db.revenue = movie.revenue

    await db.commit()
    await db.refresh(movie_db)
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_db = result.scalars().first()

    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie_db)
    await db.commit()

    return {"detail": "Movie deleted successfully."}
