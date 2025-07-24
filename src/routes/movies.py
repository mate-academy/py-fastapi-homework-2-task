import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieListItemSchema,
    MovieResponseSchema,
    MovieUpdateSchema
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    stmt_count = select(func.count()).select_from(MovieModel)
    result_count = await db.execute(stmt_count)
    total_items = result_count.scalar_one()

    total_pages = math.ceil(total_items / per_page)

    if total_items == 0 or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt_movies = select(MovieModel).offset((page - 1) * per_page).limit(per_page).order_by(MovieModel.id.desc())
    result_movies = await db.execute(stmt_movies)
    movies = result_movies.scalars().all()

    full_path = request.url.path
    base_path = full_path.replace("/api/v1", "")
    query_params = f"per_page={per_page}"

    next_page = (
        f"{base_path}?page={page + 1}&{query_params}"
        if page < total_pages else None
    )
    prev_page = (
        f"{base_path}?page={page - 1}&{query_params}"
        if page > 1 else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def get_or_create_country(session: AsyncSession, code: str):
    result = await session.execute(select(CountryModel).where(CountryModel.code == code))
    country = result.scalar()
    if not country:
        country = CountryModel(code=code, name=None)
        session.add(country)
        await session.flush()
    return country


async def get_or_create_genre(session: AsyncSession, name: str):
    result = await session.execute(select(GenreModel).where(GenreModel.name == name))
    genre = result.scalar()
    if not genre:
        genre = GenreModel(name=name)
        session.add(genre)
        await session.flush()
    return genre


async def get_or_create_actor(session: AsyncSession, name: str):
    result = await session.execute(select(ActorModel).where(ActorModel.name == name))
    actor = result.scalar()
    if not actor:
        actor = ActorModel(name=name)
        session.add(actor)
        await session.flush()
    return actor


async def get_or_create_language(session: AsyncSession, name: str):
    result = await session.execute(select(LanguageModel).where(LanguageModel.name == name))
    language = result.scalar()
    if not language:
        language = LanguageModel(name=name)
        session.add(language)
        await session.flush()
    return language


@router.post("/movies/", response_model=MovieResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieCreateSchema, session: AsyncSession = Depends(get_db)):

    query = select(MovieModel).where(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date)
    result = await session.execute(query)
    if result.scalar():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country = await get_or_create_country(session, movie_data.country)

    genres = [await get_or_create_genre(session, name) for name in movie_data.genres]

    actors = [await get_or_create_actor(session, name) for name in movie_data.actors]

    languages = [await get_or_create_language(session, name) for name in movie_data.languages]

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
    session.add(new_movie)
    await session.commit()
    await session.refresh(new_movie)

    fully_loaded_movie_result = await session.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )

    fully_loaded_movie = fully_loaded_movie_result.unique().scalar_one()

    return fully_loaded_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    movie_result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )

    movie = movie_result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    return MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    movie_to_delete = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = movie_to_delete.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
        movie_id: int,
        movie_update_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    movie_to_update = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = movie_to_update.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    update_data = movie_update_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input data: {e}")

    return {"detail": "Movie updated successfully."}
