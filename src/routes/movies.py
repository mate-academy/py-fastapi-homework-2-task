from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db, MovieModel
from src.database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from src.schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    CountrySchema,
    GenreSchema,
    ActorSchema,
    LanguageSchema,
)

PAGE_QUERY = Query(1, ge=1)
PER_PAGE_QUERY = Query(10, ge=1, le=20)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = PAGE_QUERY,
    per_page: int = PER_PAGE_QUERY,
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    base_path = "/theater/movies/"
    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"{base_path}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    duplicate = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    if duplicate.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country_result = await db.execute(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    country = country_result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        await db.flush()
        await db.refresh(country)

    genres = []
    for genre_name in movie.genres:
        genre_result = await db.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre = genre_result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
            await db.refresh(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor_result = await db.execute(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        actor = actor_result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
            await db.refresh(actor)
        actors.append(actor)

    languages = []
    for lang_name in movie.languages:
        lang_result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == lang_name)
        )
        language = lang_result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=lang_name)
            db.add(language)
            await db.flush()
            await db.refresh(language)
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

    country_data = {
        "id": getattr(country, "id", None),
        "code": getattr(country, "code", None),
        "name": getattr(country, "name", None),
    }
    genres_data = [
        {"id": getattr(g, "id", None), "name": getattr(g, "name", None)} for g in genres
    ]
    actors_data = [
        {"id": getattr(a, "id", None), "name": getattr(a, "name", None)} for a in actors
    ]
    languages_data = [
        {"id": getattr(lang, "id", None), "name": getattr(lang, "name", None)}
        for lang in languages
    ]

    response_payload = {
        "id": new_movie.id,
        "name": new_movie.name,
        "date": new_movie.date,
        "score": new_movie.score,
        "overview": new_movie.overview,
        "status": new_movie.status,
        "budget": new_movie.budget,
        "revenue": new_movie.revenue,
        "country": country_data,
        "genres": genres_data,
        "actors": actors_data,
        "languages": languages_data,
    }

    return response_payload


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int, update_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(movie, field, value)

    if movie.score < 0 or movie.score > 100 or movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    await db.commit()
    return {"detail": "Movie updated successfully."}
