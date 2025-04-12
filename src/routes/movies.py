from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailSchema, MovieCreateSchema, MovieUpdateSchema

from sqlalchemy import text


router = APIRouter()


@router.get("/debug/db-check")
async def check_db_connection(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar_one()
        return {"status": "success", "result": value}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page"),
):
    offset = (page - 1) * per_page
    total_items = await db.scalar(select(func.count(MovieModel.id)))

    movies_query = await db.execute(
        select(MovieModel)
        .offset(offset)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    movies = movies_query.scalars()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page) if total_items else 0

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # If a movie with the same name and date already exists,
    # the endpoint returns a 409 Conflict error with an appropriate message.
    stmt = select(MovieModel).where(
        and_(
            MovieModel.name == data.name,
            MovieModel.date == data.date
        )
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{data.name}' "
                   f"and release date '{data.date}' already exists."
        )

    genres_obj = []
    actors_obj = []
    languages_obj = []

    # Country data link or create
    result = await db.execute(
        select(CountryModel)
        .where(CountryModel.code == data.country)
    )
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=data.country)
        db.add(country)
        await db.flush()

    # Genres data link or create
    for genre_name in data.genres:
        result = await db.execute(
            select(GenreModel)
            .where(GenreModel.name == genre_name)
        )
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genres_obj.append(genre)

    # Actors data link or create
    for actor_name in data.actors:
        result = await db.execute(
            select(ActorModel)
            .where(ActorModel.name == actor_name)
        )
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        actors_obj.append(actor)

    # Languages data link or create
    for language_name in data.languages:
        result = await db.execute(
            select(LanguageModel)
            .where(LanguageModel.name == language_name)
        )
        language = result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()

        languages_obj.append(language)

    new_movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country=country,
        genres=genres_obj,
        actors=actors_obj,
        languages=languages_obj,
    )

    try:
        db.add(new_movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="The input data is invalid "
                   "(e.g., missing required fields, invalid values)."
        )
    else:
        await db.refresh(new_movie)
        stmt = (
            select(MovieModel)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),  # Will use separate queries
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
            .where(MovieModel.id == new_movie.id)
        )
        result = await db.execute(stmt)
        new_movie = result.scalars().first()

    return new_movie


# Movie Detail endpoint
@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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

    return movie


@router.delete("/movies/{movie_id}/")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return Response(content=None, status_code=204)


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(movie_id: int, data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = data.dict(exclude_unset=True)
    for name, value in update_data.items():
        setattr(movie, name, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
