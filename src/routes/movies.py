from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import (
    MovieModel, CountryModel, GenreModel,
    ActorModel, LanguageModel, get_db
)
from src.schemas.movies import (
    MovieDetailSchema, MovieCreateSchema,
    MovieUpdateSchema, MovieListItemSchema
)

router = APIRouter()


async def get_or_create(db: AsyncSession, model, **kwargs):
    result = await db.execute(select(model).filter_by(**kwargs))
    obj = result.scalars().first()
    if not obj:
        obj = model(**kwargs)
        db.add(obj)
    return obj


@router.post(
    "/movies/",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieDetailSchema
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        exists = (await db.execute(select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        ))).scalar_one_or_none()

        if exists:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"A movie with the name '{movie_data.name}' "
                    f"and release date '{movie_data.date.isoformat()}' already exists."
                )
            )

        country = await get_or_create(db, CountryModel, code=movie_data.country)
        genres = [await get_or_create(db, GenreModel, name=g) for g in movie_data.genres]
        actors = [await get_or_create(db, ActorModel, name=a) for a in movie_data.actors]
        languages = [
            await get_or_create(db, LanguageModel, name=lang)
            for lang in movie_data.languages
        ]

        new_movie = MovieModel(
            **movie_data.model_dump(exclude={"country", "genres", "actors", "languages"}),
            country=country, genres=genres, actors=actors, languages=languages
        )
        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie)

        movie = (await db.execute(
            select(MovieModel)
            .where(MovieModel.id == new_movie.id)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
        )).scalar_one()

        return MovieDetailSchema.model_validate(movie)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/movies/")
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    total_items = (await db.execute(select(func.count(MovieModel.id)))).scalar_one()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = (await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )).scalars().all()

    return {
        "movies": [MovieListItemSchema.model_validate(m) for m in movies],
        "total_items": total_items,
        "total_pages": total_pages,
        "prev_page": (
            f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
        ),
        "next_page": (
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
    }


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = (await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )).scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailSchema.model_validate(movie)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    update_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    movie = (await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )).scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    try:
        data = update_data.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="Invalid input data.")

        for key, value in data.items():
            setattr(movie, key, value)

        await db.commit()
        return {"detail": "Movie updated successfully."}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = (await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )).scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
