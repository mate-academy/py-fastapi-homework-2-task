from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.database.session_postgresql import get_db
from src.database.models import (
    MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
)
from src.schemas.movies import (
    MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema,
    MovieCreateSchema, MovieUpdateSchema
)

router = APIRouter()

@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    page: int = Query(1, ge=1, description="Номер сторінки, починаючи з 1"),
    per_page: int = Query(10, ge=1, le=20, description="Кількість записів на сторінці"),
    db: AsyncSession = Depends(get_db),
):
    total_items_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page

    if total_items == 0:
        return MovieListResponseSchema(
            movies=[],
            prev_page=None,
            next_page=None,
            total_pages=0,
            total_items=0
        )

    if page > total_pages and total_pages != 0:
        raise HTTPException(status_code=404, detail="Movies not found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="Movies not found.")

    base_url = str(request.url).split("?")[0]

    def make_page_url(p):
        if 1 <= p <= total_pages:
            return f"{base_url}?page={p}&per_page={per_page}"
        return None

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.from_orm(movie) for movie in movies],
        prev_page=make_page_url(page - 1) if page > 1 else None,
        next_page=make_page_url(page + 1) if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )

@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie

@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_in: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # Перевіряємо чи існує країна
    country = await db.get(CountryModel, movie_in.country_id)
    if not country:
        raise HTTPException(status_code=400, detail="Country not found")

    # Вибираємо жанри, акторів, мови
    genres = []
    if movie_in.genre_ids:
        result = await db.execute(select(GenreModel).where(GenreModel.id.in_(movie_in.genre_ids)))
        genres = result.scalars().all()
    actors = []
    if movie_in.actor_ids:
        result = await db.execute(select(ActorModel).where(ActorModel.id.in_(movie_in.actor_ids)))
        actors = result.scalars().all()
    languages = []
    if movie_in.language_ids:
        result = await db.execute(select(LanguageModel).where(LanguageModel.id.in_(movie_in.language_ids)))
        languages = result.scalars().all()

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie

@router.patch("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def update_movie(movie_id: int, movie_in: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie_in.name is not None:
        movie.name = movie_in.name
    if movie_in.date is not None:
        movie.date = movie_in.date
    if movie_in.score is not None:
        movie.score = movie_in.score
    if movie_in.overview is not None:
        movie.overview = movie_in.overview
    if movie_in.status is not None:
        movie.status = movie_in.status
    if movie_in.budget is not None:
        movie.budget = movie_in.budget
    if movie_in.revenue is not None:
        movie.revenue = movie_in.revenue

    if movie_in.country_id is not None:
        country = await db.get(CountryModel, movie_in.country_id)
        if not country:
            raise HTTPException(status_code=400, detail="Country not found")
        movie.country = country

    if movie_in.genre_ids is not None:
        result = await db.execute(select(GenreModel).where(GenreModel.id.in_(movie_in.genre_ids)))
        movie.genres = result.scalars().all()

    if movie_in.actor_ids is not None:
        result = await db.execute(select(ActorModel).where(ActorModel.id.in_(movie_in.actor_ids)))
        movie.actors = result.scalars().all()

    if movie_in.language_ids is not None:
        result = await db.execute(select(LanguageModel).where(LanguageModel.id.in_(movie_in.language_ids)))
        movie.languages = result.scalars().all()

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie

@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return None
