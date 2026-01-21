import math
from fastapi import APIRouter, Depends, HTTPException, Query
from httpx import Response

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel


from schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema, MovieCreateResponseSchema, \
    MovieUpdateResponseSchema
from routes.helpers import create_country, create_languages, create_actors, create_genres


router = APIRouter()

# Write your code here


async def get_num_movies(db: AsyncSession):
    num = select(func.count()).select_from(MovieModel)
    return await db.scalar(num)


# Write your code here
@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_all_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    total_items = await get_num_movies(db=db)
    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page

    movies_per_page = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country))
        .order_by(MovieModel.id.desc()).limit(per_page).offset(offset))
    movies_to_show = movies_per_page.scalars().all()
    result = [MovieDetailResponseSchema.model_validate(m) for m in movies_to_show]

    if movies_to_show:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

        return MovieListResponseSchema(
            movies=result,
            prev_page=prev_page,
            next_page=next_page,
            total_pages=total_pages,
            total_items=total_items
        )
    else:
        raise HTTPException(status_code=404, detail="No movies found.")


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel).where(
        MovieModel.id == movie_id).options(
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
        selectinload(MovieModel.country)
    ))
    if movie:
        return MovieDetailResponseSchema.model_validate(movie)

    else:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=201
)
async def create_movie(movie: MovieCreateResponseSchema, db: AsyncSession = Depends(get_db)):
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
    else:
        country = await create_country(movie.country, db)
        languages = await create_languages(movie.languages, db)
        genres = await create_genres(movie.genres, db)
        actors = await create_actors(movie.actors, db)

        db_movie = MovieModel(
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
            languages=languages
        )
        db.add(db_movie)
        await db.commit()
        await db.refresh(db_movie)

        result = await db.execute(
            select(MovieModel)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
            .where(MovieModel.id == db_movie.id)
        )
        db_movie_full = result.scalar_one()

        return MovieDetailResponseSchema.model_validate(db_movie_full)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_delete = result.scalar_one_or_none()
    if movie_to_delete:
        await db.delete(movie_to_delete)
        await db.commit()
        return Response(status_code=204)
    else:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
        movie_id: int,
        movie: MovieUpdateResponseSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_update = result.scalar_one_or_none()
    if movie_to_update:
        try:
            if movie.name:
                movie_to_update.name = movie.name
            if movie.date:
                movie_to_update.date = movie.date
            if movie.score is not None:
                movie_to_update.score = movie.score
            if movie.overview:
                movie_to_update.overview = movie.overview
            if movie.status:
                movie_to_update.status = movie.status
            if movie.budget is not None:
                movie_to_update.budget = movie.budget
            if movie.revenue is not None:
                movie_to_update.revenue = movie.revenue
            await db.commit()
            await db.refresh(movie_to_update)
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=400, detail="Invalid input data.")
        return {"detail": "Movie updated successfully."}
    else:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
