from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieStatusEnum
from schemas import (
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieListResponseSchema,
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
        request: Request,
        page: int = Query(1, ge=1, description="Page number (minimum 1)"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page (from 1 to 20)"),
        db: AsyncSession = Depends(get_db)
):
    count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    movies_result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = [
        MovieListItemSchema.model_validate(movie, from_attributes=True)
        for movie in movies_result.scalars().all()
    ]

    base_path = "/theater/movies/"
    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_path}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        total_pages=total_pages,
        total_items=total_items,
        prev_page=prev_page,
        next_page=next_page,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    if isinstance(movie.status, str):
        try:
            movie.status = MovieStatusEnum(movie.status)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid status value in the database.")

    return MovieDetailSchema.model_validate(movie, from_attributes=True)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_in: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    duplicate_stmt = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date
    )
    duplicate_result = await db.execute(duplicate_stmt)
    existing_movie = duplicate_result.scalars().first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists."
        )

    try:
        status_enum = MovieStatusEnum(movie_in.status)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid status value.")

    country_stmt = select(CountryModel).where(CountryModel.code == movie_in.country)
    country_result = await db.execute(country_stmt)
    country_obj = country_result.scalars().first()
    if not country_obj:
        country_obj = CountryModel(code=movie_in.country, name=movie_in.country)
        db.add(country_obj)
        await db.flush()

    genre_objs = []
    for genre_name in movie_in.genres:
        stmt = select(GenreModel).where(GenreModel.name == genre_name)
        res = await db.execute(stmt)
        genre_obj = res.scalars().first()
        if not genre_obj:
            genre_obj = GenreModel(name=genre_name)
            db.add(genre_obj)
            await db.flush()
        genre_objs.append(genre_obj)

    actor_objs = []
    for actor_name in movie_in.actors:
        stmt = select(ActorModel).where(ActorModel.name == actor_name)
        res = await db.execute(stmt)
        actor_obj = res.scalars().first()
        if not actor_obj:
            actor_obj = ActorModel(name=actor_name)
            db.add(actor_obj)
            await db.flush()
        actor_objs.append(actor_obj)

    language_objs = []
    for language_name in movie_in.languages:
        stmt = select(LanguageModel).where(LanguageModel.name == language_name)
        res = await db.execute(stmt)
        language_obj = res.scalars().first()
        if not language_obj:
            language_obj = LanguageModel(name=language_name)
            db.add(language_obj)
            await db.flush()
        language_objs.append(language_obj)

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=status_enum,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country_obj
    )
    new_movie.genres = genre_objs
    new_movie.actors = actor_objs
    new_movie.languages = language_objs

    db.add(new_movie)
    await db.commit()
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    new_movie = result.scalars().first()
    return MovieDetailSchema.model_validate(new_movie, from_attributes=True)


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie_in: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_in.model_dump(exclude_unset=True)
    if "status" in update_data:
        try:
            update_data["status"] = MovieStatusEnum(update_data["status"])
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid status value.")

    for field, value in update_data.items():
        setattr(movie, field, value)

    db.add(movie)
    await db.commit()
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return
