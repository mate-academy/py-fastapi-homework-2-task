from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import MovieModel
from schemas import MovieListResponseSchema, MovieCreateSchema
from sqlalchemy.orm import joinedload
from fastapi import HTTPException


async def get_movies(
        db: AsyncSession,
        page: int,
        per_page: int,
):
    offset = (page - 1) * per_page

    total_items_stmt = select(func.count()).select_from(MovieModel)
    result = await db.execute(total_items_stmt)
    total_items = result.scalar_one()

    total_pages = (total_items + per_page - 1) // per_page

    stmt = (
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    prev_page = None if page <= 1 else f"/theater/movies/?page={page-1}&per_page={per_page}"
    next_page = None if page >= total_pages else f"/theater/movies/?page={page+1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def get_movie_by_id(db: AsyncSession, movie_id):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    result = await db.execute(stmt)
    movie = result.unique().scalar_one_or_none()
    return movie


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    new_movie = MovieModel(**movie.model_dump())

    question = await db.execute(select(MovieModel).filter_by(name=movie.name))
    existing_movie = question.scalar_one_or_none()

    if existing_movie is not None:
        raise HTTPException(status_code=409, detail="This film already exists.")

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie