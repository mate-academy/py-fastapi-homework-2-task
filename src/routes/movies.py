from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel, GenreModel, ActorModel, LanguageModel, CountryModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter()


async def get_or_create_models(db: AsyncSession, model_class, ids: list[int], names: list[str]) -> list:
    result_models = []
    if ids:
        q = await db.execute(select(model_class).where(model_class.id.in_(ids)))
        result_models.extend(q.scalars().all())

    if names:
        existing_q = await db.execute(select(model_class).where(model_class.name.in_(names)))
        existing = existing_q.scalars().all()
        existing_names = {e.name for e in existing}
        new_names = set(names) - existing_names
        new_models = [model_class(name=n) for n in new_names]
        db.add_all(new_models)
        await db.flush()
        await db.commit()
        result_models.extend(existing)
        result_models.extend(new_models)

    return result_models


async def load_movie_with_relations(db: AsyncSession, movie_id: int) -> MovieModel | None:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return result.unique().scalar_one_or_none()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page not found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    prev_page = f"/theater/movies/?page={page-1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page+1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(m) for m in movies],
        total_items=total_items,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await load_movie_with_relations(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return MovieDetailSchema.model_validate(movie)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    exists_query = await db.execute(
        select(MovieModel).where(MovieModel.name == data.name, MovieModel.date == data.date)
    )
    if exists_query.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists.",
        )

    if data.country_id:
        country_id = data.country_id
    elif data.country:
        country_id = await db.scalar(select(CountryModel.id).where(CountryModel.code == data.country))
        if not country_id:
            new_country = CountryModel(code=data.country, name=None)
            db.add(new_country)
            await db.flush()
            country_id = new_country.id
    else:
        country_id = await db.scalar(select(CountryModel.id).limit(1))

    movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country_id=country_id,
    )
    db.add(movie)
    await db.flush()

    movie = await load_movie_with_relations(db, movie.id)

    movie.genres = await get_or_create_models(db, GenreModel, [], data.genres or [])
    movie.actors = await get_or_create_models(db, ActorModel, [], data.actors or [])
    movie.languages = await get_or_create_models(db, LanguageModel, [], data.languages or [])

    await db.commit()

    movie = await load_movie_with_relations(db, movie.id)
    return MovieDetailSchema.model_validate(movie)


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "genres":
            movie.genres = await get_or_create_models(db, GenreModel, [], value or [])
        elif field == "actors":
            movie.actors = await get_or_create_models(db, ActorModel, [], value or [])
        elif field == "languages":
            movie.languages = await get_or_create_models(db, LanguageModel, [], value or [])
        else:
            setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None
