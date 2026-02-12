from math import ceil
from typing import List, Type

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Query,
    status
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas import (
    MovieListResponseSchema,
    MovieDetailSchema
)
from schemas.movies import (
    MovieCreateResponseSchema,
    MovieCreateRequestSchema,
    MovieUpdateSchema
)

router = APIRouter()


# Write your code here
@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = ceil(total_items / per_page)
    if total_items == 0 or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."

        )
    movies = await db.scalars(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    next_page, prev_page = None, None
    if (page * per_page) < total_items:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    return {
        "movies": movies.all(),
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post(
    "/movies/",
    response_model=MovieCreateResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
        movie: MovieCreateRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    db_movie = await db.scalar(
        select(MovieModel)
        .where(
            (MovieModel.name == movie.name) & (MovieModel.date == movie.date)
        )
    )
    if db_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = await db.scalar(
        select(CountryModel).where(
            func.upper(CountryModel.code) == movie.country.upper())
    )
    if not country:
        country = CountryModel(code=movie.country, name=movie.country)
        db.add(country)
        await db.flush()

    async def get_or_create_entities(
            model: Type[GenreModel | ActorModel | LanguageModel],
            names: List[str]
    ) -> List:
        entities = []
        for name in names:
            entity = await db.scalar(select(model).where(model.name == name))
            if not entity:
                entity = model(name=name)
                db.add(entity)
                await db.flush()
            entities.append(entity)
        return entities

    genres = await get_or_create_entities(GenreModel, movie.genres)
    actors = await get_or_create_entities(ActorModel, movie.actors)
    languages = await get_or_create_entities(LanguageModel, movie.languages)

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
    query = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
    )
    result = await db.execute(query)
    return result.scalar_one()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
    )

    movie = await db.scalar(query)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    await db.delete(db_movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def movie_update(
        movie_id: int,
        update_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_movie = update_data.model_dump(exclude_unset=True)

    for key, value in update_movie.items():
        setattr(db_movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
