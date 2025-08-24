from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieUpdateSchema,
    MoviesListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema
)

from crud.movies import get_movie_by_id, update_movie_partial, delete_movie

router = APIRouter()


@router.get("/movies/", response_model=MoviesListResponseSchema)
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    total_items = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items.scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    )

    return MoviesListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    q = await db.execute(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    existing = q.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    # Country
    country_q = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = country_q.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        await db.flush()

    # Genres
    genres = []
    for g in movie.genres:
        g_q = await db.execute(select(GenreModel).where(GenreModel.name == g))
        genre = g_q.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=g)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    # Actors
    actors = []
    for a in movie.actors:
        a_q = await db.execute(select(ActorModel).where(ActorModel.name == a))
        actor = a_q.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=a)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    # Languages
    languages = []
    for lang_name in movie.languages:
        l_q = await db.execute(select(LanguageModel).where(LanguageModel.name == lang_name))
        lang = l_q.scalar_one_or_none()
        if not lang:
            lang = LanguageModel(name=lang_name)
            db.add(lang)
            await db.flush()
        languages.append(lang)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    q = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    movie_with_relations = q.scalar_one()
    return movie_with_relations


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def movie_detail(movie_id: int, session: AsyncSession = Depends(get_db)):
    return await get_movie_by_id(session, movie_id)


@router.patch("/movies/{movie_id}/")
async def patch_movie(
        movie_id: int,
        movie_update: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    update_data = movie_update.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )

    await update_movie_partial(db, movie_id, update_data)

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    await delete_movie(db, movie_id)
    return None
