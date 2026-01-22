from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListItemSchema,
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieUpdateSchema
)


router = APIRouter()


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):

    query = select(MovieModel).where(
        and_(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    existing = await db.execute(query)
    existing_movie = existing.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    country_res = await db.execute(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    country_obj = country_res.scalar_one_or_none()
    if not country_obj:
        country_obj = CountryModel(code=movie.country, name=None)
        db.add(country_obj)
        await db.flush()

    genres_objs = []
    for genre_name in movie.genres:
        genre_res = await db.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre_obj = genre_res.scalar_one_or_none()
        if not genre_obj:
            genre_obj = GenreModel(name=genre_name)
            db.add(genre_obj)
            await db.flush()
        genres_objs.append(genre_obj)

    actors_objs = []
    for actor_name in movie.actors:
        actor_res = await db.execute(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        actor_obj = actor_res.scalar_one_or_none()
        if not actor_obj:
            actor_obj = ActorModel(name=actor_name)
            db.add(actor_obj)
            await db.flush()
        actors_objs.append(actor_obj)

    languages_objs = []
    for lang_name in movie.languages:
        lang_res = await db.execute(
            select(LanguageModel).where(LanguageModel.name == lang_name)
        )
        lang_obj = lang_res.scalar_one_or_none()
        if not lang_obj:
            lang_obj = LanguageModel(name=lang_name)
            db.add(lang_obj)
            await db.flush()
        languages_objs.append(lang_obj)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country_obj,
        genres=genres_objs,
        actors=actors_objs,
        languages=languages_objs,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

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
    movie_with_relations = result.scalar_one()

    return movie_with_relations


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema
)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
) -> MovieListResponseSchema:
    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    movies = result.scalars().all()

    movies_schema = [
        MovieListItemSchema.model_validate(movie)
        for movie in movies
    ]

    return MovieListResponseSchema(
        movies=movies_schema,
        prev_page=f"/theater/movies/?page={page - 1}&"
                  f"per_page={per_page}" if page > 1 else None,
        next_page=f"/theater/movies/?page={page + 1}&"
                  f"per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema
)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
)-> MovieDetailResponseSchema:
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    deleted_movie = result.scalar_one_or_none()
    if deleted_movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(deleted_movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK
)
async def update_movie(
        movie_id: int,
        movie: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    db_movie = result.scalar_one_or_none()

    if db_movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
