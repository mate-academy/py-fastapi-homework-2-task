from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieStatusEnum,
)
from schemas import MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema
from schemas.movies import MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    offset = (page - 1) * per_page

    count_query = select(func.count(MovieModel.id))
    result = await db.execute(count_query)
    total_items = result.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page)

    query = (
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    )
    result = await db.execute(query)
    movies = [
        MovieListItemSchema.model_validate(mov)
        for mov in result.scalars().all()
    ]

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page_url = (
        f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page_url = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=list(movies),
        prev_page=prev_page_url,
        next_page=next_page_url,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    if isinstance(movie.status, str):
        try:
            movie.status = MovieStatusEnum(movie.status)
        except ValueError:
            raise HTTPException(
                status_code=422, detail="Invalid status value in the database."
            )

    return MovieDetailSchema.model_validate(movie, from_attributes=True)


@router.post(
    "/movies/",
    status_code=201,
    response_model=MovieDetailSchema,
)
async def create_movie(
    movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    existing_stmt = select(MovieModel).where(
        (MovieModel.name == movie_data.name), (MovieModel.date == movie_data.date)
    )
    existing_result = await db.execute(existing_stmt)
    existing_movie = existing_result.scalars().first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )
    try:
        country_stmt = select(CountryModel).where(
            CountryModel.code == movie_data.country
        )
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


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_id: int, new_movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = new_movie.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)

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

    return
