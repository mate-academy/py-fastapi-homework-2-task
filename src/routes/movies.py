from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import Annotated
from starlette import status

from schemas.movies import (
    MovieDetailSchema,
    MovieCreateSchema,
    MovieListItemSchema,
    MovieUpdateSchema
)
from pagination.pages import MoviesPage
from pagination.params import Params
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()


@router.get(
    "/movies/",
)
async def get_movies(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Params = Depends(),
) -> MoviesPage[MovieListItemSchema]:
    total = (await db.scalar(select(func.count()).select_from(MovieModel)))
    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )
    total_pages = (total + params.per_page - 1) // params.per_page
    if params.page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found.",
        )
    return await paginate(
        db,
        select(MovieModel).order_by(desc(MovieModel.id)),
        params=params,
        additional_data={
            "request": request
        }
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie with the given ID was not found."}}
            },
        }
    },
)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = (await db.execute(stmt)).scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return MovieDetailSchema.model_validate(movie)


@router.post("/movies/", status_code=201)
async def create_movie(
        movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name, MovieModel.date == movie_data.date
        )
    )
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' "
                   f"and release date '{movie_data.date}' already exists.",
        )
    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie_data.country)
    )
    try:
        if not country:
            country = CountryModel(code=movie_data.country, name=None)
            db.add(country)
            await db.flush()
        genres = []
        for genre_name in movie_data.genres:
            genre = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)
        actors = []
        for actor_name in movie_data.actors:
            actor = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)
        languages = []
        for language_name in movie_data.languages:
            language = await db.scalar(select(LanguageModel).where(LanguageModel.name == language_name))
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()
            languages.append(language)
        new_movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        db.add(new_movie)
        await db.commit()

        return new_movie
    except IntegrityError:
        await db.rollback()

        raise HTTPException(status_code=400, detail="Invalid input data")


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not result:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(result)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    result = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not result:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    update_data = movie.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(result, key, value)

    await db.commit()
    await db.refresh(result)
    return {"detail": "Movie updated successfully."}
