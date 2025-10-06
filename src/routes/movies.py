from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (MovieCreateItemSchema, MovieCreateResponseSchema,
                            MovieDetailResponseSchema, MovieListResponseSchema,
                            MovieUpdateSchema)

router = APIRouter()


async def get_or_create_entity(db: AsyncSession, model, name: str):
    result = await db.execute(select(model).where(model.name == name))
    entity = result.scalar_one_or_none()

    if entity:
        return entity

    code = name[:3].upper() if hasattr(model, "code") else None

    new_entity = model(name=name, code=code) if code else model(name=name)
    db.add(new_entity)
    await db.commit()
    await db.refresh(new_entity)

    return new_entity


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )

    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
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


@router.post("/movies/", response_model=MovieCreateResponseSchema, status_code=201)
async def create_movie(
    movie: MovieCreateItemSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    existing_movie = result.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country = await get_or_create_entity(db, CountryModel, movie.country)

    genres = []
    for genre_name in movie.genres:
        genre = await get_or_create_entity(db, GenreModel, genre_name)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = await get_or_create_entity(db, ActorModel, actor_name)
        actors.append(actor)

    languages = []
    for lang_name in movie.languages:
        language = await get_or_create_entity(db, LanguageModel, lang_name)
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
    try:
        await db.commit()
        await db.refresh(new_movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Failed to create movie due to integrity error."
        )

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    new_movie_with_relations = result.scalar_one()

    return new_movie_with_relations


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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

    return


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    updated_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    for field, value in updated_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
