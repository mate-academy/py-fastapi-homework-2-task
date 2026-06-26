import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    count_stmt = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(payload: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    dup_stmt = select(MovieModel).where(MovieModel.name == payload.name, MovieModel.date == payload.date)
    dup_result = await db.execute(dup_stmt)
    if dup_result.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists."
        )

    try:
        country_stmt = select(CountryModel).where(CountryModel.code == payload.country)
        country_res = await db.execute(country_stmt)
        country = country_res.scalars().first()
        if not country:
            country = CountryModel(code=payload.country, name=None)
            db.add(country)
            await db.flush()

        genres_list = []
        for g_name in payload.genres:
            g_stmt = select(GenreModel).where(GenreModel.name == g_name)
            g_res = await db.execute(g_stmt)
            genre = g_res.scalars().first()
            if not genre:
                genre = GenreModel(name=g_name)
                db.add(genre)
            genres_list.append(genre)

        actors_list = []
        for a_name in payload.actors:
            a_stmt = select(ActorModel).where(ActorModel.name == a_name)
            a_res = await db.execute(a_stmt)
            actor = a_res.scalars().first()
            if not actor:
                actor = ActorModel(name=a_name)
                db.add(actor)
            actors_list.append(actor)

        languages_list = []
        for l_name in payload.languages:
            l_stmt = select(LanguageModel).where(LanguageModel.name == l_name)
            l_res = await db.execute(l_stmt)
            lang = l_res.scalars().first()
            if not lang:
                lang = LanguageModel(name=l_name)
                db.add(lang)
            languages_list.append(lang)

        await db.flush()

        new_movie = MovieModel(
            name=payload.name,
            date=payload.date,
            score=payload.score,
            overview=payload.overview,
            status=payload.status,
            budget=payload.budget,
            revenue=payload.revenue,
            country_id=country.id,
            genres=genres_list,
            actors=actors_list,
            languages=languages_list
        )

        db.add(new_movie)
        await db.commit()

        stmt = (
            select(MovieModel)
            .options(
                joinedload(MovieModel.country),
                joinedload(MovieModel.genres),
                joinedload(MovieModel.actors),
                joinedload(MovieModel.languages)
            )
            .where(MovieModel.id == new_movie.id)
        )
        final_res = await db.execute(stmt)
        return final_res.scalars().first()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, payload: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
