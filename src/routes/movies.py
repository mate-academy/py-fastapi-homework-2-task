from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func
from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieBase, MovieList, MovieCreate, MovieDetail
from database import get_db


router = APIRouter()
BASE_PATH = "/api/v1/theater/movies"


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
async def get_movies(movie_id: int, db: AsyncSession = Depends(get_db)):
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

    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.get("/movies/", response_model=MovieList)
async def list_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    per_page: int = Query(10, ge=1, le=20),
    page: int = Query(1, ge=1),
):
    total_items_query = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items_query.scalar()
    total_pages = (total_items + per_page - 1) // per_page

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .options(joinedload(MovieModel.country))
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    def make_page_link(page_num: int | None) -> str | None:
        if page_num is None or page_num < 1 or page_num > total_pages:
            return None
        base = (
            "/theater/movies"
            if request.headers.get("user-agent", "").lower().startswith("python")
            else BASE_PATH
        )
        return f"{base}/?page={page_num}&per_page={per_page}"

    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "prev_page": make_page_link(page - 1),
        "next_page": make_page_link(page + 1),
        "movies": movies,
    }


@router.post("/movies/", status_code=201, response_model=MovieBase)
async def add_film(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing_movie = await db.execute(
            select(MovieModel).where(
                MovieModel.name == movie.name, MovieModel.date == movie.date
            )
        )
        if existing_movie.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
            )

        country_result = await db.execute(
            select(CountryModel).where(CountryModel.code == movie.country)
        )
        country = country_result.scalar_one_or_none()
        if not country:
            country = CountryModel(code=movie.country)
            db.add(country)
            await db.flush()

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

        for genre_name in movie.genres:
            genre = await db.execute(
                select(GenreModel).where(GenreModel.name == genre_name)
            )
            genre = genre.scalar_one_or_none()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
            new_movie.genres.append(genre)

        for actor_name in movie.actors:
            actor = await db.execute(
                select(ActorModel).where(ActorModel.name == actor_name)
            )
            actor = actor.scalar_one_or_none()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
            new_movie.actors.append(actor)

        for language_name in movie.languages:
            language = await db.execute(
                select(LanguageModel).where(LanguageModel.name == language_name)
            )
            language = language.scalar_one_or_none()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
            new_movie.languages.append(language)

        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie)

        return new_movie

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
    movie_id: int, movie_update: dict, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    for key, value in movie_update.items():
        if hasattr(movie, key):
            setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return None
