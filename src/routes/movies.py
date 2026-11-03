from datetime import datetime, timedelta
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

import schemas
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()


@router.get("/movies/", response_model=schemas.movies.MovieListResponseSchema)
async def movies_list(page: int = Query(1, ge=1),
                      per_page: int = Query(10, ge=1, le=20),
                      db: AsyncSession = Depends(get_db)):
    count_movies = await db.scalar(select(func.count(MovieModel.id)))

    if not count_movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    total_pages = math.ceil(count_movies / per_page)

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    else:
        prev_page = None

    if total_pages >= page + 1:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"
    else:
        next_page = None

    skip = (page - 1) * per_page

    all_movie = (await db.scalars(select(
        MovieModel).offset(skip).limit(
        per_page).order_by(MovieModel.id.desc()))).all()

    return {
        "movies": all_movie,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": count_movies
    }


@router.post("/movies/", response_model=schemas.movies.MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def movie_create(movie_data: schemas.movies.MovieCreate, db: AsyncSession = Depends(get_db)):
    name = movie_data.name
    if len(name) > 255:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    if movie_data.date > (datetime.now() + timedelta(days=365)).date():
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    if movie_data.score > 100 or movie_data.score < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    if movie_data.budget < 0 or movie_data.revenue < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    query_for_check_name_and_date = select(
        MovieModel).where(
        (MovieModel.name == f"{movie_data.name}") & (MovieModel.date == movie_data.date))
    check_movie_with_name_and_date = await db.scalar(query_for_check_name_and_date)

    if check_movie_with_name_and_date:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country_info = movie_data.country
    country_query = select(CountryModel).where(CountryModel.code == country_info)
    res_for_country = await db.scalar(country_query)
    country_obj = res_for_country
    if res_for_country is None:
        country_obj = CountryModel(code=country_info)
        db.add(country_obj)
        await db.commit()
        await db.refresh(country_obj)

    list_with_genres = []
    list_with_actors = []
    list_with_languages = []

    for genre in movie_data.genres:
        genre_obj = await db.scalar(select(GenreModel).where(GenreModel.name == genre))
        if genre_obj is None:
            genre_obj = GenreModel(name=genre)
            db.add(genre_obj)
            await db.commit()
            await db.refresh(genre_obj)
        list_with_genres.append(genre_obj)

    for actor in movie_data.actors:
        actor_obj = await db.scalar(select(ActorModel).where(ActorModel.name == actor))
        if actor_obj is None:
            actor_obj = ActorModel(name=actor)
            db.add(actor_obj)
            await db.commit()
            await db.refresh(actor_obj)
        list_with_actors.append(actor_obj)

    for language in movie_data.languages:
        language_obj = await db.scalar(select(LanguageModel).where(LanguageModel.name == language))
        if language_obj is None:
            language_obj = LanguageModel(name=language)
            db.add(language_obj)
            await db.commit()
            await db.refresh(language_obj)
        list_with_languages.append(language_obj)

    create_movie = MovieModel(
        **movie_data.model_dump(exclude={"country", "genres", "actors", "languages"}),
        country=country_obj,
        genres=list_with_genres,
        actors=list_with_actors,
        languages=list_with_languages
    )

    db.add(create_movie)
    await db.commit()
    await db.refresh(create_movie,
                     attribute_names=["country", "genres", "actors", "languages"]
                     )
    return create_movie


@router.get("/movies/{movie_id}/", response_model=schemas.movies.MovieDetailSchema)
async def movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.scalar(select(MovieModel).options(selectinload(MovieModel.country),
                                                        selectinload(MovieModel.genres),
                                                        selectinload(MovieModel.actors),
                                                        selectinload(MovieModel.languages),
                                                        ).where(MovieModel.id == movie_id)
                             )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return result


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def movie_delete(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(result)
    await db.commit()

    return


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def movie_update(movie_id: int, data: schemas.movies.MovieUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.get(MovieModel, movie_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    if data.score is not None:
        if data.score > 100 or data.score < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid input data."
            )
    if data.budget is not None:
        if data.budget < 0 or data.revenue < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid input data."
            )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(result, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
