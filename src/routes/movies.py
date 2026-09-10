import math
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])
movie_router = router


def _movie_eager_load_options():
    return [
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ]


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count(MovieModel.id))
    count_res = await db.execute(count_stmt)
    total_items = count_res.scalar() or 0

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    offset = (page - 1) * per_page
    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    res = await db.execute(stmt)
    movies = res.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieDetailResponseSchema,
)
async def create_movie(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    try:
        movie_in = MovieCreateSchema(**payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    stmt = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date,
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists.",
        )

    country_obj = None
    if movie_in.country:
        c_stmt = select(CountryModel).where(CountryModel.code == movie_in.country)
        c_res = await db.execute(c_stmt)
        country_obj = c_res.scalar_one_or_none()
        if not country_obj:
            country_obj = CountryModel(code=movie_in.country)
            db.add(country_obj)
            await db.flush()

    genre_objs = []
    for g_name in movie_in.genres:
        g_stmt = select(GenreModel).where(GenreModel.name == g_name)
        g_res = await db.execute(g_stmt)
        g_obj = g_res.scalar_one_or_none()
        if not g_obj:
            g_obj = GenreModel(name=g_name)
            db.add(g_obj)
            await db.flush()
        genre_objs.append(g_obj)

    actor_objs = []
    for a_name in movie_in.actors:
        a_stmt = select(ActorModel).where(ActorModel.name == a_name)
        a_res = await db.execute(a_stmt)
        a_obj = a_res.scalar_one_or_none()
        if not a_obj:
            a_obj = ActorModel(name=a_name)
            db.add(a_obj)
            await db.flush()
        actor_objs.append(a_obj)

    lang_objs = []
    for l_name in movie_in.languages:
        l_stmt = select(LanguageModel).where(LanguageModel.name == l_name)
        l_res = await db.execute(l_stmt)
        l_obj = l_res.scalar_one_or_none()
        if not l_obj:
            l_obj = LanguageModel(name=l_name)
            db.add(l_obj)
            await db.flush()
        lang_objs.append(l_obj)

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country_obj,
        genres=genre_objs,
        actors=actor_objs,
        languages=lang_objs,
    )
    db.add(new_movie)
    await db.commit()

    fetch_stmt = (
        select(MovieModel)
        .options(*_movie_eager_load_options())
        .where(MovieModel.id == new_movie.id)
    )
    fetch_res = await db.execute(fetch_stmt)
    created_movie = fetch_res.scalar_one()

    return created_movie


@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MovieModel)
        .options(*_movie_eager_load_options())
        .where(MovieModel.id == movie_id)
    )
    res = await db.execute(stmt)
    movie = res.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    res = await db.execute(stmt)
    movie = res.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    try:
        update_data = MovieUpdateSchema(**payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    res = await db.execute(stmt)
    movie = res.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_dict = (
        update_data.model_dump(exclude_unset=True)
        if hasattr(update_data, "model_dump")
        else update_data.dict(exclude_unset=True)
    )

    for key, value in update_dict.items():
        setattr(movie, key, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
