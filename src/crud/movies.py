from fastapi import (
    HTTPException,
    Request,
    Query,
)
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.responses import JSONResponse

from crud.utils.resolve_movie_relations import (
    resolve_movie_relations
)
from database import MovieModel
from schemas.movies import (
    MovieCreate,
    MovieUpdate, MoviePatch
)


async def get_movies(
        request: Request,
        db: AsyncSession,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
):
    curr_offset = (page - 1) * per_page
    movies_result = await db.execute(
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(curr_offset)
        .limit(per_page)
    )
    movies = movies_result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    count_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_movies = count_result.scalar()
    total_pages = (total_movies + per_page - 1) // per_page

    url_path = request.url.path
    query_base = f"{url_path}"
    prev_page = f"{query_base}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{query_base}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_movies,
        "movies": movies
    }


async def get_movie(movie_id: int, db: AsyncSession):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return result.scalar_one_or_none()


async def create_movie(movie: MovieCreate, db: AsyncSession):
    data = movie.model_dump()

    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    relation_data = await resolve_movie_relations(data, db)

    new_movie = MovieModel(**{
        k: v for k, v in data.items()
        if k not in {"country", "genres", "actors", "languages"}
    })

    new_movie.country = relation_data["country"]
    new_movie.genres = relation_data["genres"]
    new_movie.actors = relation_data["actors"]
    new_movie.languages = relation_data["languages"]

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )

    return result.scalar_one()


async def update_movie(
    movie_id: int,
    updated_movie: MovieUpdate | MoviePatch,
    db: AsyncSession
) -> JSONResponse:
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    data = updated_movie.model_dump(exclude_unset=True)

    relation_data = await resolve_movie_relations(data, db)

    if "country" in relation_data:
        movie.country = relation_data["country"]
    if "genres" in relation_data:
        movie.genres = relation_data["genres"]
    if "actors" in relation_data:
        movie.actors = relation_data["actors"]
    if "languages" in relation_data:
        movie.languages = relation_data["languages"]

    for field in ["country", "genres", "actors", "languages"]:
        data.pop(field, None)

    for field, value in data.items():
        setattr(movie, field, value)

    await db.commit()
    await db.refresh(movie)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "Movie updated successfully."
        }
    )


async def delete_movie(
        movie_id: int,
        db: AsyncSession
) -> None:
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return None
