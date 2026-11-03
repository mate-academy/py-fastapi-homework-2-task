from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MessageResponseSchema
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1,),
    per_page: int = Query(10, ge=1, le=20,),
    db: AsyncSession = Depends(get_db)
):

    count_stmt = select(func.count(MovieModel.id))
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
):

    stmt = select(CountryModel).where(CountryModel.code == movie_data.country)
    result = await db.execute(stmt)
    country = result.scalars().first()

    if not country:
        country = CountryModel(code=movie_data.country, name=None)
        db.add(country)
        await db.flush()

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id
    )

    for genre_name in movie_data.genres:
        stmt = select(GenreModel).where(GenreModel.name == genre_name)
        result = await db.execute(stmt)
        genre = result.scalars().first()

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()

        new_movie.genres.append(genre)

    for actor_name in movie_data.actors:
        stmt = select(ActorModel).where(ActorModel.name == actor_name)
        result = await db.execute(stmt)
        actor = result.scalars().first()

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()

        new_movie.actors.append(actor)

    for language_name in movie_data.languages:
        stmt = select(LanguageModel).where(LanguageModel.name == language_name)
        result = await db.execute(stmt)
        language = result.scalars().first()

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()

        new_movie.languages.append(language)

    db.add(new_movie)

    try:
        await db.commit()
        await db.refresh(new_movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    stmt = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
    )
    result = await db.execute(stmt)
    movie_with_relations = result.scalars().first()

    return movie_with_relations


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):

    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return None


@router.patch("/movies/{movie_id}/", response_model=MessageResponseSchema)
async def update_movie(
    movie_id: int,
    update_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(movie, field, value)

    await db.commit()

    return MessageResponseSchema(detail="Movie updated successfully.")
