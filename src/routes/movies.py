from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional

from src.database import get_db, MovieModel
from src.database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from src.schemas import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailResponseSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retrieve a paginated list of movies."""

    total_item_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = int(total_item_result.scalar_one())

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().unique().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    base_url = "/theater/movies/"
    prev_page: Optional[str] = None
    next_page: Optional[str] = None

    if page > 1:
        prev_page = f"{base_url}?page={page-1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"{base_url}?page={page+1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
    movie_id: int, db: AsyncSession = Depends(get_db)
) -> MovieModel:
    """Retrieve a single movie by its ID."""
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    movie_dict = movie_data.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )
    new_movie = MovieModel(**movie_dict)

    # --- Country ---
    country_result = await db.execute(
        select(CountryModel).where(CountryModel.code == movie_data.country)
    )
    country_obj = country_result.scalars().first()
    if not country_obj:
        country_obj = CountryModel(code=movie_data.country)
        db.add(country_obj)
        # raise HTTPException(status_code=404, detail="Country not found")
    new_movie.country = country_obj

    # --- Genres ---
    if movie_data.genres:
        new_genres = []
        for genre_name in movie_data.genres:
            genre_result = await db.execute(
                select(GenreModel).where(GenreModel.name == genre_name)
            )
            genre = genre_result.scalars().first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                new_genres.append(genre)
        if new_genres:
            await db.flush()  # flush once for all new genres

        genres_result = await db.execute(
            select(GenreModel).where(GenreModel.name.in_(movie_data.genres))
        )
        new_movie.genres = genres_result.scalars().all()

    # --- Actors ---
    if movie_data.actors:
        new_actors = []
        for actor_name in movie_data.actors:
            actor_result = await db.execute(
                select(ActorModel).where(ActorModel.name == actor_name)
            )
            actor = actor_result.scalars().first()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                new_actors.append(actor)
        if new_actors:
            await db.flush()

        actors_result = await db.execute(
            select(ActorModel).where(ActorModel.name.in_(movie_data.actors))
        )
        new_movie.actors = actors_result.scalars().all()

    # --- Languages ---
    if movie_data.languages:
        new_languages = []
        for language_name in movie_data.languages:
            lang_result = await db.execute(
                select(LanguageModel).where(LanguageModel.name == language_name)
            )
            language = lang_result.scalars().first()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                new_languages.append(language)
        if new_languages:
            await db.flush()

        languages_result = await db.execute(
            select(LanguageModel).where(LanguageModel.name.in_(movie_data.languages))
        )
        new_movie.languages = languages_result.scalars().all()

    db.add(new_movie)
    try:
        await db.commit()
        await db.refresh(
            new_movie, attribute_names=["genres", "actors", "languages", "country"]
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{new_movie.name}' and release date '{new_movie.date}' already exists.",
        )

    return new_movie


@router.patch("/movies/{movie_id}/", response_model=dict)
async def update_movie(
    movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        # .options(
        #     selectinload(MovieModel.genres),
        #     selectinload(MovieModel.actors),
        #     selectinload(MovieModel.languages),
        #     selectinload(MovieModel.country),
        # )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    movie_dict = movie_data.model_dump(
        exclude_unset=True,
        exclude={"country", "genres", "actors", "languages"},
    )
    for key, value in movie_dict.items():
        setattr(movie, key, value)

    try:
        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()

    return None
