from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from math import ceil

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, get_or_create
from schemas.movies import MovieUpdateSchema, MovieCreatedResponse, MovieCreate


router = APIRouter()


@router.get("/movies/")#, response_model=MovieListItemSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = max(1, ceil(total_items / per_page))
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=MovieCreatedResponse)
async def create_movie(data: MovieCreate, db: AsyncSession = Depends(get_db)):
    async with db.begin():  # автоматичний commit/rollback
        # Перевірка дублікату
        result = await db.execute(
            select(MovieModel).where(MovieModel.name == data.name, MovieModel.date == data.date)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists."
            )

        # Country
        country = await get_or_create(db, CountryModel, code=data.country)

        # Movie
        movie = MovieModel(
            name=data.name,
            date=data.date,
            score=data.score,
            overview=data.overview,
            status=data.status,
            budget=data.budget,
            revenue=data.revenue,
            country_id=country.id,
        )
        db.add(movie)
        # await db.flush()  # отримати movie.id

        movie.genres = []
        for name in data.genres:
            genre = await get_or_create(db, GenreModel, name=name)
            movie.genres.append(genre)

        movie.actors = []
        for name in data.actors:
            actor = await get_or_create(db, ActorModel, name=name)
            movie.actors.append(actor)

        movie.languages = []
        for name in data.languages:
            language = await get_or_create(db, LanguageModel, name=name)
            movie.languages.append(language)

        await db.refresh(movie)

    return MovieCreatedResponse.model_validate(movie)



@router.get("/movies/{movie_id}/", response_model=MovieCreatedResponse)
async def get_movie_detail(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(
            MovieModel.id == movie_id,
        )
    )

    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Movie with the given ID was not found."
            )
        )


    return MovieCreatedResponse.model_validate(movie)


@router.delete("/movies/{movie_id}/")
async def delete_movie_(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(MovieModel)
        .where(
            MovieModel.id == movie_id,
        )
    )

    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    # 1️⃣ Retrieve movie
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    # 4️⃣ Commit changes safely
    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
