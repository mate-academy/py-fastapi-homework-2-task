import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import crud

from database.models import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from database.session_postgresql import get_postgresql_db

from schemas.movies import MoviesListSchema, MovieDetailSchema, MovieCreateSchema, MoviePatchSchema
from sources.movie_create import (
    check_if_movie_exist,
    get_or_create_country,
    get_or_create_entity,
    create_movie_instance,
    get_movie_or_404,
)

router = APIRouter()


@router.get("/movies/", response_model=MoviesListSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_postgresql_db)
):
    # Порахувати всі елементи, щоб можна було потім їх розприділити по сторінках
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    # Вичисляємо загальну кільксть сторінок, навіть при умові що сторнка може бути не повна і містити іншу кількість
    # елементів
    total_pages = math.ceil(total_items / per_page)

    # визначаємо offcet тобто к-сть записів які ми будемо зміщувати при вибірці
    offset = (page - 1) * per_page
    # ну і нарешті проводимо саму вибірку
    movies = await db.query(MovieModel).offset(offset).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Це list comprehension, який перетворює список об'єктів movies (отриманих з бази даних через SQLAlchemy) у
    # список об'єктів-схем типу MovieDetailResponseSchema
    movies_schema = [MovieDetailSchema.model_validate(movie, from_attributes=True) for movie in movies]

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MoviesListSchema(
        movies=movies_schema,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_postgresql_db)
):
    await check_if_movie_exist(movie.name, movie.date, db)

    country = await get_or_create_country(None, movie.country, db)
    genres = await get_or_create_entity(GenreModel, movie.genres, db)
    actors = await get_or_create_entity(ActorModel, movie.actors, db)
    languages = await get_or_create_entity(LanguageModel, movie.languages, db)

    new_movie = create_movie_instance(None, movie, country, genres, actors, languages)

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return MovieDetailSchema.model_validate(new_movie, from_attributes=True)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_postgresql_db)
):
    movie = await get_movie_or_404(movie_id, db)
    return MovieDetailSchema.model_validate(movie, from_attributes=True)


@router.patch("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def update_movie(
        movie_id: int,
        movie_data: MoviePatchSchema,
        db: AsyncSession = Depends(get_postgresql_db)
):
    movie = await get_movie_or_404(movie_id, db)

    if movie.name == movie_data.name or movie.date == movie_data.date:
        await check_if_movie_exist(movie.name, movie.date, db)

    if (movie_data.name and movie_data.name != movie.name) or (movie_data.date and movie_data.date != movie.date):
        name_to_check = movie_data.name or movie.name
        date_to_check = movie_data.date or movie.date
        await check_if_movie_exist(name_to_check, date_to_check, db, movie_id=movie_id)

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        if field not in {"country", "genres", "actors", "languages"}:
            setattr(movie, field, value)

    if movie_data.country:
        movie.country = await get_or_create_country(name=None, code=movie_data.country, db=db)

    if movie_data.genres:
        movie.genres = await get_or_create_entity(GenreModel, movie_data.genres, db)

    if movie_data.actors:
        movie.actors = await get_or_create_entity(ActorModel, movie_data.actors, db)

    if movie_data.languages:
        movie.languages = await get_or_create_entity(LanguageModel, movie_data.languages, db)

    await db.commit()
    await db.refresh(movie)
    return MovieDetailSchema.model_validate(movie, from_attributes=True)


@router.delete("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_postgresql_db)
):
    movie = await get_or_create_entity(MovieModel, movie_id)
    await db.delete(movie)
    await db.commit()
    return MovieDetailSchema.model_validate(movie, from_attributes=True)
