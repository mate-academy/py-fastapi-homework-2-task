from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
)
from repository import (
    get_movie,
    get_movie_or_404,
    get_movies,
    get_number_of_movies,
    get_or_create,
)
from schemas import (
    MovieCreateRequestSchema,
    MovieCreateResponseSchema,
    MovieErrorSchema,
    MovieListResponseSchema,
    MovieUpdateRequestSchema,
    MovieUpdateResponseShema,
)

router = APIRouter(prefix="/movies")


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "model": MovieErrorSchema,
            "description": "No movies found."
        }
    }
)
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
) -> MovieListResponseSchema:
    movies = await get_movies(per_page, page, db)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await get_number_of_movies(db)
    total_pages = (total_items - 1) // per_page + 1
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema.model_validate(
        {
            "movies": movies,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_items": total_items,
        }
    )


@router.post(
    "/",
    response_model=MovieCreateResponseSchema,
    status_code=201,
    responses={
        409: {
            "model": MovieErrorSchema,
            "description": "Movie already exists",
        }
    }
)
async def create_movie(
        movie: MovieCreateRequestSchema,
        db: AsyncSession = Depends(get_db),
) -> MovieCreateResponseSchema:
    movie_exists = await get_movie(db=db, name=movie.name, date=movie.date)

    if movie_exists:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    country = await get_or_create(CountryModel, db, code=movie.country)
    genres = [await get_or_create(GenreModel, db, name=name) for name in movie.genres]
    actors = [await get_or_create(ActorModel, db, name=name) for name in movie.actors]
    languages = [await get_or_create(LanguageModel, db, name=name) for name in movie.languages]

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
    new_movie = await get_movie(db, id=new_movie.id)

    return MovieCreateResponseSchema.model_validate(new_movie)


@router.get(
    "/{movie_id}/",
    response_model=MovieCreateResponseSchema,
    responses={
        404: {
            "model": MovieErrorSchema,
            "description": "Movie with the given ID was not found."
        }
    }
)
async def movie_detail(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieCreateResponseSchema:
    movie = await get_movie_or_404(movie_id, db)
    return MovieCreateResponseSchema.model_validate(movie)


@router.delete(
    "/{movie_id}/",
    status_code=204,
    responses={
        404: {
            "model": MovieErrorSchema,
            "description": "Movie with the given ID was not found."
        }
    }
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> None:
    movie = await get_movie_or_404(movie_id, db)
    await db.delete(movie)
    await db.commit()


@router.patch(
    "/{movie_id}/",
    response_model=MovieUpdateResponseShema,
    responses={
        400: {
            "model": MovieErrorSchema,
            "description": "Invalid input data."
        },
        404: {
            "model": MovieErrorSchema,
            "description": "Movie with the given ID was not found."
        }
    }
)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateRequestSchema,
        db: AsyncSession = Depends(get_db),
) -> MovieUpdateResponseShema:

    movie = await get_movie_or_404(movie_id, db)
    data_dict = movie_data.model_dump(exclude_unset=True)

    try:
        for field, value in data_dict.items():
            setattr(movie, field, value)
        await db.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return MovieUpdateResponseShema.model_validate(
        {"detail": "Movie updated successfully."}
    )
