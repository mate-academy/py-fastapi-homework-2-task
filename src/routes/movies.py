from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from crud.movie_crud import get_or_create_country, get_or_create_many
from database import get_db
from schemas.movies import MoviesListResponse, MovieBase, MovieRead, MovieCreate, MovieUpdate, PaginatedMoviesResponse
from database.models import GenreModel, ActorModel, LanguageModel, MovieModel

router = APIRouter()


@router.get("/movies/", response_model=PaginatedMoviesResponse)
async def get_movies(page: int = Query(1, ge=1),
                     per_page: int = Query(10, ge=1, le=50),
                     db: AsyncSession = Depends(get_db)):
    total_stmt = select(func.count(MovieModel.id))
    total = (await db.execute(total_stmt)).scalar_one()
    if total == 0 or (page - 1) * per_page >= total:
        raise HTTPException(status_code=404, detail="No movies found.")
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()
    short_movies = [MovieShortSchema.model_validate(movie) for movie in movies]
    base_url = "/theater/movies/"
    prev_url = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_url = f"{base_url}?page={page + 1}&per_page={per_page}" if page * per_page < total else None

    return PaginatedMoviesResponse(
        movies=short_movies,
        prev_page=prev_url,
        next_page=next_url,
        total_pages=(total + per_page - 1) // per_page,
        total_items=total
    )


@router.get("/movies/{movie_id}/", response_model=MovieRead)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(selectinload(MovieModel.genres),
                 selectinload(MovieModel.actors),
                 selectinload(MovieModel.languages),
                 selectinload(MovieModel.country))
        .where(MovieModel.id == movie_id))
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found."
                            )
    return movie


@router.post("/movies/", response_model=MovieRead, status_code=201)
async def add_movie(movie_create: MovieCreate, db: AsyncSession = Depends(get_db)):
    # Duplicate check
    result = await db.execute(select(MovieModel).where(
        MovieModel.name == movie_create.name,
        MovieModel.date == movie_create.date
    ))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_create.name}' and release date '{movie_create.date}' already exists.")
    country = await get_or_create_country(movie_create.country, db)
    genres = await get_or_create_many(GenreModel, movie_create.genres, db)
    actors = await get_or_create_many(ActorModel, movie_create.actors, db)
    languages = await get_or_create_many(LanguageModel, movie_create.languages, db)
    new_movie = MovieModel(
        name=movie_create.name,
        date=movie_create.date,
        score=movie_create.score,
        overview=movie_create.overview,
        status=movie_create.status,
        budget=movie_create.budget,
        revenue=movie_create.revenue,
        country_id=country.id,
    )
    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages
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
    movie_with_relations = result.scalar_one()

    return movie_with_relations


@router.patch("/movies/{movie_id}/", response_model=MovieRead)
async def update_movie(movie_id: int, movie_update: MovieUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
        await db.refresh(movie)
        return movie

    except Exception as e:
        print(f"Error occurred: {e}")
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/movies/{movie_id}/")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return Response(status_code=204)
