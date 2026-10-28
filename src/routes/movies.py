import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import (
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateItemSchema,
    MovieUpdateSchema
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
        db: Annotated[AsyncSession, Depends(get_db)],
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20)
):

    result = await db.scalars(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    check_len = await db.scalar(
        select(func.count(MovieModel.id)).select_from(MovieModel)
    )

    if check_len <= 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )
    movies = result.all()
    total_items = check_len
    total_pages = (check_len + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    prev_page = None if page == 1 else (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
    )
    next_page = None if page == total_pages else (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_info: MovieCreateItemSchema
):
    movie_info = movie_info.model_dump()

    country = movie_info.pop("country")
    date = movie_info.get("date")
    genres = movie_info.pop("genres")
    actors = movie_info.pop("actors")
    languages = movie_info.pop("languages")

    max_date = datetime.date.today() + datetime.timedelta(days=365)
    if date > max_date:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    movie = MovieModel(**movie_info)

    res_country = await db.scalar(
        select(CountryModel).where(CountryModel.code == country)
    )

    if not res_country:
        res_country = CountryModel(code=country)
        db.add(res_country)
        await db.flush()

    movie.country = res_country

    genres_objects = []
    for genre in genres:
        res_genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == genre)
        )
        if not res_genre:
            res_genre = GenreModel(name=genre)
            db.add(res_genre)
            await db.flush()

        genres_objects.append(res_genre)

    actors_objects = []
    for actor in actors:
        res_actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == actor)
        )
        if not res_actor:
            res_actor = ActorModel(name=actor)
            db.add(res_actor)
            await db.flush()

        actors_objects.append(res_actor)

    languages_objects = []
    for language in languages:
        res_language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == language)
        )
        if not res_language:
            res_language = LanguageModel(name=language)
            db.add(res_language)
            await db.flush()

        languages_objects.append(res_language)

    movie.genres = genres_objects
    movie.actors = actors_objects
    movie.languages = languages_objects

    db.add(movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def detail_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.refresh(movie, attribute_names=["country", "genres", "actors", "languages"])

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int,
        movie_update_info: MovieUpdateSchema
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    for param, value in movie_update_info.model_dump(exclude_unset=True).items():
        setattr(movie, param, value)

    db.add(movie)
    await db.commit()
    await db.refresh(movie, attribute_names=["country", "genres", "actors", "languages"])

    return {"detail": "Movie updated successfully."}
