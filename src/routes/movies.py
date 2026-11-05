from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema
from schemas.movies import MovieDetailSchema, MovieCreateSchema, MovieUpdateSchema


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    count_query = select(func.count()).select_from(MovieModel)
    total_items_result = await db.execute(count_query)
    total_items = total_items_result.scalar_one()

    total_pages = ceil(total_items / per_page)

    if total_items == 0 or page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    offset = (page - 1) * per_page
    query = select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )

    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = await db.scalar(select(CountryModel).where(CountryModel.code == movie.country))
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genre_objs = []
    for g_name in movie.genres:
        genre = await db.scalar(select(GenreModel).where(GenreModel.name == g_name))
        if not genre:
            genre = GenreModel(name=g_name)
            db.add(genre)
            await db.flush()
        genre_objs.append(genre)

    actor_objs = []
    for a_name in movie.actors:
        actor = await db.scalar(select(ActorModel).where(ActorModel.name == a_name))
        if not actor:
            actor = ActorModel(name=a_name)
            db.add(actor)
            await db.flush()
        actor_objs.append(actor)

    lang_objs = []
    for l_name in movie.languages:
        lang = await db.scalar(select(LanguageModel).where(LanguageModel.name == l_name))
        if not lang:
            lang = LanguageModel(name=l_name)
            db.add(lang)
            await db.flush()
        lang_objs.append(lang)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
    )

    db.add(new_movie)
    await db.commit()

    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),  # один-до-багатьох
            selectinload(MovieModel.genres),  # багато-до-багатьох
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    for key, value in movie.model_dump(exclude_unset=True).items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()

    if db_movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(db_movie)
    await db.commit()
    return None
