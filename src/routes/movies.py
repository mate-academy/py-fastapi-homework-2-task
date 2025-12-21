from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import (
    get_db, MovieModel, CountryModel, GenreModel,
    ActorModel, LanguageModel
)
from schemas.movies import (
    MovieCreateSchema, MovieUpdateSchema,
    MovieDetailResponseSchema, MovieListResponseSchema
)

router = APIRouter(prefix="/movies", tags=["Movies"])


async def get_or_create(session, model, field, value):
    stmt = select(model).where(getattr(model, field) == value)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    if not instance:
        instance = model(**{field: value})
        session.add(instance)
    return instance


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    count_stmt = select(func.count(MovieModel.id))
    total_items = (await db.execute(count_stmt)).scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt = select(MovieModel).order_by(
        MovieModel.id.desc()
    ).offset((page - 1) * per_page).limit(per_page)

    movies = (await db.execute(stmt)).scalars().all()

    path = "/theater/movies/"
    prev = f"{path}?page={page-1}&per_page={per_page}" if page > 1 else None
    nxt = f"{path}?page={page+1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev,
        "next_page": nxt,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country = await get_or_create(db, CountryModel, "code", movie_data.country)
    genres = [await get_or_create(db, GenreModel, "name", g) for g in movie_data.genres]
    actors = [await get_or_create(db, ActorModel, "name", a) for a in movie_data.actors]
    langs = [await get_or_create(db, LanguageModel, "name", ln) for ln in movie_data.languages]

    new_movie = MovieModel(
        **movie_data.model_dump(exclude={"country", "genres", "actors", "languages"}),
        country=country,
        genres=genres,
        actors=actors,
        languages=langs
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id).options(
        selectinload(MovieModel.country), selectinload(MovieModel.genres),
        selectinload(MovieModel.actors), selectinload(MovieModel.languages)
    )
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.patch("/{movie_id}/")
async def update_movie(movie_id: int, update_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    data = update_data.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in data.items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None
