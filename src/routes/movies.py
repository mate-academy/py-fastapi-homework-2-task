from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import database
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieSchema, MovieUpdateSchema
)
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_all_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if total_items <= 0:
        raise HTTPException(status_code=404, detail="No movies found.")
    result = await db.scalars(
        select(database.models.MovieModel).order_by(
            MovieModel.id.desc()).offset(
            (page - 1) * per_page).limit(per_page)
    )
    total_pages = (total_items + per_page - 1) // per_page

    movies = result.all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    if page <= 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if total_pages <= page:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieSchema, status_code=201)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.scalar(select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    ))
    if result is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}'"
                   f" and release date '{movie_data.date}'"
                   f" already exists."
        )

    country = await db.scalar(select(CountryModel).where(
        CountryModel.code == movie_data.country)
    )

    if country is None:
        country = CountryModel(code=movie_data.country)
        db.add(country)

    genres = []
    for genre in movie_data.genres:
        result = await db.scalar(select(GenreModel).where(
            GenreModel.name == genre
        ))
        if result is None:
            result = GenreModel(name=genre)
            db.add(result)
        genres.append(result)

    actors = []
    for actor in movie_data.actors:
        result = await db.scalar(select(ActorModel).where(
            ActorModel.name == actor
        ))
        if result is None:
            result = ActorModel(name=actor)
            db.add(result)

        actors.append(result)

    languages = []
    for language in movie_data.languages:
        result = await db.scalar(select(LanguageModel).where(
            LanguageModel.name == language
        ))

        if result is None:
            result = LanguageModel(name=language)
            db.add(result)

        languages.append(result)

    exclude_fields = {"country", "genres", "actors", "languages"}
    movie_fields = movie_data.model_dump(exclude=exclude_fields)
    movie = MovieModel(
        **movie_fields,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()

    movie = await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == movie.id)
    )

    return movie


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieSchema
)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=204
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    movie = await db.scalar(select(MovieModel).where(
        MovieModel.id == movie_id
    ))
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    status_code=200
)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.scalar(select(MovieModel).where(
        MovieModel.id == movie_id
    ))

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    result = movie_data.model_dump(exclude_unset=True)

    for key, value in result.items():
        setattr(movie, key, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
