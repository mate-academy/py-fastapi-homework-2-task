from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema
from schemas.movies import MovieDetailSchema, MovieCreateItemSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=20, alias="per_page")
):
    offset = (page - 1) * size
    total_items = await db.scalar(select(func.count(MovieModel.id))) or 0
    total_pages = ceil(total_items / size)
    prev_page = f"/theater/movies/?page={page - 1}&per_page={size}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={size}" if page < total_pages else None
    movies = list(await db.scalars(select(
        MovieModel).offset(offset).limit(
        size).order_by(MovieModel.id.desc())))

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


async def get_or_create(db: AsyncSession, model, **kwargs):
    instance = await db.scalar(select(model).filter_by(**kwargs))
    if instance is None:
        instance = model(**kwargs)
        db.add(instance)
        await db.flush()
    return instance


async def get_movie_or_404(db: AsyncSession, movie_id: int):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
    ))

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie_data: MovieCreateItemSchema, db: AsyncSession = Depends(get_db)):
    try:
        country = await get_or_create(db, CountryModel, code=movie_data.country)
        genres = [await get_or_create(db, GenreModel, name=name) for name in movie_data.genres]
        actors = [await get_or_create(db, ActorModel, name=name) for name in movie_data.actors]
        languages = [await get_or_create(db, LanguageModel, name=name) for name in movie_data.languages]

        movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages
        )
        db.add(movie)

        await db.commit()
        await db.refresh(movie)
        return await get_movie_or_404(db, movie.id)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' "
                   f"and release date '{movie_data.date}' already exists."
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def retrieve_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    return await get_movie_or_404(db, movie_id)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_or_404(db, movie_id)

    await db.delete(movie)
    await db.commit()

    return Response(status_code=204)


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie_or_404(db, movie_id)
    try:
        for field, value in movie_data.model_dump(exclude_unset=True).items():
            setattr(movie, field, value)
        await db.commit()
        await db.refresh(movie)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
