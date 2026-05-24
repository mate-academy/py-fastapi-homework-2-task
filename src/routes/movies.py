import math
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieDetailSchema
from schemas.movies import MovieListResponseSchema, MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    total = await db.execute(select(func.count(MovieModel.id)))
    total_items = total.scalar()
    total_pages = math.ceil(total_items / per_page)

    result = await db.execute(select(MovieModel).order_by(
        MovieModel.id.desc()).offset((page - 1) * per_page).limit(
        per_page))
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    existing_movie = await db.execute(
        select(MovieModel)
        .where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )
    if existing_movie.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}'"
                   f" and release date '{movie.date}' already exists."
        )

    country = await db.execute(
        select(CountryModel)
        .where(
            CountryModel.code == movie.country,
        )
    )
    country = country.scalars().first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for genre_name in movie.genres:
        genre = await db.execute(
            select(GenreModel)
            .where(GenreModel.name == genre_name)
        )
        genre = genre.scalars().first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for actors_name in movie.actors:
        actor = await db.execute(
            select(ActorModel)
            .where(ActorModel.name == actors_name)
        )
        actor = actor.scalars().first()
        if not actor:
            actor = ActorModel(name=actors_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = await db.execute(
            select(LanguageModel)
            .where(LanguageModel.name == language_name)
        )
        language = language.scalars().first()
        if not language:
            language = LanguageModel(name=language_name)
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
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    new_movie = result.scalars().first()
    return new_movie


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    updated_movie = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
    )
    updated_movie = updated_movie.scalars().first()
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie.name is not None:
        updated_movie.name = movie.name
    if movie.date is not None:
        updated_movie.date = movie.date
    if movie.score is not None:
        updated_movie.score = movie.score
    if movie.overview is not None:
        updated_movie.overview = movie.overview
    if movie.status is not None:
        updated_movie.status = movie.status
    if movie.budget is not None:
        updated_movie.budget = movie.budget
    if movie.revenue is not None:
        updated_movie.revenue = movie.revenue

    await db.commit()
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(db_movie)
    await db.commit()
    return Response(status_code=204)
