import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import schemas
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def get_movies(page: int = Query(1, ge=1),
                     per_page: int = Query(10, ge=1, le=20),
                     db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    count = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = count.scalar()
    total_pages = math.ceil(total_items / per_page)

    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"
    else:
        next_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    else:
        prev_page = None
    return {"movies": movies,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_items": total_items}


@router.post("/movies/", status_code=201,
             response_model=schemas.MovieDetailResponseSchema)
async def create_movie(movie_data: schemas.MovieCreateRequestSchema,
                       db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.name == movie_data.name,
                                                       MovieModel.date == movie_data.date))
    movies = result.scalar_one_or_none()
    if movies:
        raise HTTPException(status_code=409,
                            detail=f"A movie with the name '{movie_data.name}' "
                                   f"and release date '{movie_data.date}' already exists.")

    country_result = await db.execute(select(CountryModel).
                                      where(CountryModel.code == movie_data.country))
    db_country = country_result.scalar_one_or_none()
    if not db_country:
        db_country = CountryModel(code=movie_data.country)

    db_genres = []
    for genre_name in movie_data.genres:
        genre_result = await db.execute(select(GenreModel).
                                        where(GenreModel.name == genre_name))
        db_genre = genre_result.scalar_one_or_none()
        if not db_genre:
            db_genre = GenreModel(name=genre_name)
        db_genres.append(db_genre)

    db_actors = []
    for actor_name in movie_data.actors:
        actor_result = await db.execute(select(ActorModel).
                                        where(ActorModel.name == actor_name))
        db_actor = actor_result.scalar_one_or_none()
        if not db_actor:
            db_actor = ActorModel(name=actor_name)
        db_actors.append(db_actor)

    db_languages = []
    for lang_name in movie_data.languages:
        lang_result = await db.execute(select(LanguageModel).
                                       where(LanguageModel.name == lang_name))
        db_lang = lang_result.scalar_one_or_none()
        if not db_lang:
            db_lang = LanguageModel(name=lang_name)
        db_languages.append(db_lang)

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=db_country,  # Assigning the object we found/created
        genres=db_genres,  # Assigning the list of objects we built
        actors=db_actors,  # Assigning the list of objects we built
        languages=db_languages  # Assigning the list of objects we built
    )

    db.add(new_movie)
    await db.commit()

    final_result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    complete_movie = final_result.unique().scalar_one()

    return complete_movie


@router.get("/movies/{movie_id}/",
            response_model=schemas.MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int,
                       movie_data: schemas.MovieUpdateRequestSchema,
                       db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    update_data = movie_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
