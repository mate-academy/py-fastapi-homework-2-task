from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import math

from src.database import get_db
from src.database.models import (
    MovieModel, CountryModel, GenreModel,
    ActorModel, LanguageModel
)
from schemas.movies import (
    MovieListResponseSchema, MovieCreateSchema,
    MovieDetailSchema, MovieUpdateSchema
)

router = APIRouter(prefix="/movies", tags=["Movies"])


# [1] Implement Movies List Endpoint
@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    count_query = select(func.count(MovieModel.id))
    total_items = (await db.execute(count_query)).scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies_query = (
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(movies_query)
    movies = result.scalars().all()

    # base_url = str(request.url).split('?')[0]
    # prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    # next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

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


# [2] Implement Movie Creation Endpoint
@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_in: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # Перевірка на дублікат
    dup_query = select(MovieModel).where(MovieModel.name == movie_in.name, MovieModel.date == movie_in.date)
    if (await db.execute(dup_query)).scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists."
        )

    async def get_or_create_related(model, names):
        objs = []
        for name in names:
            res = await db.execute(select(model).where(model.name == name))
            obj = res.scalar_one_or_none()
            if not obj:
                obj = model(name=name)
                db.add(obj)
            objs.append(obj)
        return objs

    res_country = await db.execute(select(CountryModel).where(CountryModel.code == movie_in.country))
    country = res_country.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie_in.country)
        db.add(country)

    await db.flush()

    new_movie = MovieModel(
        **movie_in.model_dump(exclude={"genres", "actors", "languages", "country"}),
        country_id=country.id
    )

    new_movie.genres = await get_or_create_related(GenreModel, movie_in.genres)
    new_movie.actors = await get_or_create_related(ActorModel, movie_in.actors)
    new_movie.languages = await get_or_create_related(LanguageModel, movie_in.languages)

    db.add(new_movie)
    await db.commit()

    final_res = await db.execute(
        select(MovieModel)
        .options(selectinload(MovieModel.genres), selectinload(MovieModel.actors),
                 selectinload(MovieModel.languages), selectinload(MovieModel.country))
        .where(MovieModel.id == new_movie.id)
    )
    return final_res.scalar_one()


# [3] Implement Movie Details Endpoint
@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .options(selectinload(MovieModel.genres), selectinload(MovieModel.actors),
                 selectinload(MovieModel.languages), selectinload(MovieModel.country))
        .where(MovieModel.id == movie_id)
    )
    movie = (await db.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


# [4] Implement Movie Deletion Endpoint
@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()


# [5] Implement Movie Update Endpoint
@router.patch("/{movie_id}/")
async def update_movie(movie_id: int, movie_in: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie_db = await db.get(MovieModel, movie_id)
    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update_data.items():
        setattr(movie_db, key, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
