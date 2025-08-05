from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select, func, desc, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import JSONResponse

from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieRead,
    MovieUpdateSchema,
    MovieReadSchema,
    MovieCreateSchema
)

router = APIRouter()


# utils
async def get_or_create_entity(session: AsyncSession, model, name_or_code: str, field="name"):
    stmt = select(model).where(getattr(model, field) == name_or_code)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        return instance

    instance = model(**{field: name_or_code})
    session.add(instance)
    await session.flush()
    return instance


@router.get("/movies", response_model=MovieListResponseSchema)
async def get_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):

    total_items_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items_result.scalar()
    total_pages = (total_items + per_page - 1) // per_page

    base_url = str(request.url).split("?")[0]
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .offset(offset)
        .limit(per_page)
        .order_by(desc(MovieModel.id))
    )
    movies = result.scalars().all()

    return MovieListResponseSchema(
        movies=[MovieRead.from_orm(m) for m in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieReadSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # Check for duplicates
    existing_movie = await db.execute(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    if existing_movie.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    # Get or create related entities
    country = await get_or_create_entity(db, CountryModel, movie.country, field="code")
    genres = [await get_or_create_entity(db, GenreModel, g) for g in movie.genres]
    actors = [await get_or_create_entity(db, ActorModel, a) for a in movie.actors]
    languages = [await get_or_create_entity(db, LanguageModel, l) for l in movie.languages]  # noqa: E741

    # Create movie
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
        languages=languages
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(stmt)
    movie_with_relationships = result.scalar_one()

    return MovieReadSchema.model_validate(movie_with_relationships)


@router.get("/movies/{movie_id}", response_model=MovieReadSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)

    movie_with_relationships = result.scalar_one_or_none()

    if not movie_with_relationships:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieReadSchema.model_validate(movie_with_relationships)


@router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(delete(MovieModel).where(MovieModel.id == movie_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.commit()
    return Response(status_code=204)


@router.patch("/movies/{movie_id}")
async def update_movie(
    movie_id: int,
    update_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_fields = update_data.model_dump(exclude_unset=True)

    if not update_fields:
        return JSONResponse(status_code=200, content={"detail": "Nothing to update."})

    try:
        await db.execute(
            update(MovieModel)
            .where(MovieModel.id == movie_id)
            .values(**update_fields)
        )
        await db.commit()
        return JSONResponse(status_code=200, content={"detail": "Movie updated successfully."})

    except Exception:
        # Log exception if needed
        raise HTTPException(status_code=400, detail="Invalid input data.")
