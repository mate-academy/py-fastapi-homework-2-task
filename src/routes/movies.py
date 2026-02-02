from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import MovieModel, GenreModel, ActorModel, LanguageModel, CountryModel
from schemas.movies import (
    MoviePaginationSchema, MovieDetailSchema,
    MovieCreateSchema, MovieUpdateSchema
)

router = APIRouter()


@router.get("/", response_model=MoviePaginationSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page

    total_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_result.scalar()

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/theater/movies/"
    return {
        "movies": movies,
        "total_items": total_items,
        "total_pages": total_pages,
        "next_page": f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "prev_page": f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    }

async def get_movie_by_id(movie_id: int, db: AsyncSession):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    return result.scalars().first()

@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(movie_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # Перевірка на конфлікт (409)
    duplicate_check = await db.execute(
        select(MovieModel).where(and_(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date))
    )
    if duplicate_check.scalar():
        raise HTTPException(status_code=409, detail="Movie with this name and date already exists.")

    country_obj = None
    if movie_data.country:
        res = await db.execute(select(CountryModel).where(CountryModel.name == movie_data.country))
        country_obj = res.scalars().first()

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country_obj
    )

    async def get_or_create_entities(model, names_list):
        entities = []
        for name in names_list:
            res = await db.execute(select(model).where(model.name == name))
            obj = res.scalars().first()
            if not obj:
                obj = model(name=name)
                db.add(obj)
            entities.append(obj)
        return entities

    new_movie.genres = await get_or_create_entities(GenreModel, movie_data.genres)
    new_movie.actors = await get_or_create_entities(ActorModel, movie_data.actors)
    new_movie.languages = await get_or_create_entities(LanguageModel, movie_data.languages)

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return await get_movie_by_id(new_movie.id, db)


@router.patch("/{movie_id}/")
async def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for key, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."} #


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None