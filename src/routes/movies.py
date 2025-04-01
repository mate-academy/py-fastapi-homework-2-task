from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema
)
from schemas.movies import MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "description": "No movies found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."}
                }
            },
        }
    }
)
async def get_movie_list(
        page: int = Query(1, ge=1, description="Page number (1-based index)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    offset = (page - 1) * per_page

    count_stmt = select(func.count(MovieModel.id))
    result_count = await db.execute(count_stmt)
    total_items = result_count.scalar() or 0

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    order_by = MovieModel.default_order_by()
    stmt = select(MovieModel)
    if order_by:
        stmt = stmt.order_by(*order_by)

    stmt = stmt.offset(offset).limit(per_page)

    result_movies = await db.execute(stmt)
    movies = result_movies.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list = [MovieListItemSchema.model_validate(movie) for movie in movies]

    total_pages = (total_items + per_page - 1) // per_page

    response = MovieListResponseSchema(
        movies=movie_list,
        prev_page=f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )
    return response


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    responses={
        201: {
            "description": "Movie created successfully.",
        },
        400: {
            "description": "Invalid input.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input data."}
                }
            },
        }
    },
    status_code=201
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    existing_stmt = select(MovieModel).where(
        (MovieModel.name == movie_data.name),
        (MovieModel.date == movie_data.date)
    )
    existing_result = await db.execute(existing_stmt)
    existing_movie = existing_result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            )
        )

    try:
        country_stmt = select(CountryModel).where(CountryModel.code == movie_data.country)
        country_result = await db.execute(country_stmt)
        country = country_result.scalars().first()
        if not country:
            country = CountryModel(code=movie_data.country)
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie_data.genres:
            genre_stmt = select(GenreModel).where(GenreModel.name == genre_name)
            genre_result = await db.execute(genre_stmt)
            genre = genre_result.scalars().first()

            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        actors = []
        for actor_name in movie_data.actors:
            actor_stmt = select(ActorModel).where(ActorModel.name == actor_name)
            actor_result = await db.execute(actor_stmt)
            actor = actor_result.scalars().first()

            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)

        languages = []
        for language_name in movie_data.languages:
            lang_stmt = select(LanguageModel).where(LanguageModel.name == language_name)
            lang_result = await db.execute(lang_stmt)
            language = lang_result.scalars().first()

            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()
            languages.append(language)

        movie = MovieModel(
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
        db.add(movie)
        await db.commit()
        await db.refresh(movie, ["genres", "actors", "languages"])

        return MovieDetailSchema.model_validate(movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        }
    }
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

    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.model_validate(movie)


@router.delete(
    "/movies/{movie_id}/",
    responses={
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    },
    status_code=204
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    responses={
        200: {
            "description": "Movie updated successfully.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie updated successfully."}
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    }
)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
