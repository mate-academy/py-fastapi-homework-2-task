from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import JSONResponse

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_list(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
) -> MovieListResponseSchema:
    offset = (page - 1) * per_page

    result = await db.scalars(select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page))

    movies = list(result.all())

    total_movies = await db.scalar(select(func.count()).select_from(MovieModel))

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_movies + per_page - 1) // per_page

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    response = {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_movies,
    }
    return response


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_film(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    result = await db.execute(
        select(MovieModel).options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        ).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


async def create_new_item(
        items: list[str],
        model: GenreModel | ActorModel | LanguageModel,
        db: AsyncSession = Depends(get_db),
) -> list:
    result = []
    for item_name in items:
        item = await db.scalar(select(model).where(model.name == item_name))
        if not item:
            item = model(name=item_name)
            db.add(item)
            await db.flush()
        result.append(item)
    return result


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    movie_list = await db.scalars(select(MovieModel).where(MovieModel.name == movie.name))
    existing_movies = movie_list.all()

    if any(existing_movie.date == movie.date for existing_movie in existing_movies):
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = await db.scalar(select(CountryModel).where(CountryModel.code == movie.country))
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=await create_new_item(movie.genres, GenreModel, db=db),
        actors=await create_new_item(movie.actors, ActorModel, db=db),
        languages=await create_new_item(movie.languages, LanguageModel, db=db),
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(MovieModel).options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        ).where(MovieModel.id == new_movie.id)
    )
    result_movie = result.scalars().first()

    return result_movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
        movie_id: int,
        movie: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie_to_update = result.scalars().first()
    if not movie_to_update:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    if movie.name:
        movie_to_update.name = movie.name
    if movie.date:
        movie_to_update.date = movie.date
    if movie.score:
        movie_to_update.score = movie.score
    if movie.overview:
        movie_to_update.overview = movie.overview
    if movie.status:
        movie_to_update.status = movie.status
    if movie.budget:
        movie_to_update.budget = movie.budget
    if movie.revenue:
        movie_to_update.revenue = movie.revenue

    await db.commit()
    await db.refresh(movie_to_update)
    return {"detail": "Movie updated successfully."}
