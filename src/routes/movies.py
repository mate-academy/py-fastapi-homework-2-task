from math import ceil

from sqlalchemy.orm import selectinload

from urllib.parse import urlparse
from schemas.countries import CountryResponseSchema
from src.database.models import GenreModel, ActorModel, Base, LanguageModel, CountryModel
from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.movies import MovieListItemSchema, MoviePatchSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from fastapi import Request

from src.database import get_db, MovieModel
from src.schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieResponseSchema
from starlette import status
from typing_extensions import Type

router = APIRouter()


# Write your code here
@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_list(
        request: Request,
        page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items = await db.execute(select(func.count()).select_from(MovieModel))
    total_items_count = total_items.scalar() or 0
    total_pages = ceil(total_items_count / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")
    base_url = str(request.url_for("get_movies_list")).split("/api/v1", 1)[-1]
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    start_item_number = (page - 1) * per_page
    result_query = await (db
                          .execute(select(MovieModel)
                                   .order_by(MovieModel.id.desc())
                                   .slice(start_item_number, start_item_number + per_page))
                          )
    result = result_query.scalars().all()

    if not result:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = [MovieListItemSchema.model_validate(movie) for movie in result]
    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_items=total_items_count,
        total_pages=total_pages
    )


@router.get("/movies/{movie_id}/", response_model=MovieResponseSchema)
async def get_movie_by_id(
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
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/movies/", response_model=MovieResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie: MovieDetailSchema,
        db: AsyncSession = Depends(get_db),
):
    existing_movie = await db.execute(select(MovieModel.id).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ))
    if existing_movie.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    existing_country = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country_instance = existing_country.scalar_one_or_none()
    if country_instance is None:
        country_instance = CountryModel(code=movie.country)
        db.add(country_instance)
        await db.flush()

    genres = await attach_entities(movie.genres, GenreModel, db)
    actors = await attach_entities(movie.actors, ActorModel, db)
    languages = await attach_entities(movie.languages, LanguageModel, db)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country_instance.id,
        genres=genres,
        actors=actors,
        languages=languages
    )
    db.add(new_movie)

    await db.commit()
    await db.refresh(new_movie)

    return MovieResponseSchema(
        id=new_movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=CountryResponseSchema.model_validate(country_instance),
        genres=genres,
        actors=actors,
        languages=languages
    )


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_film(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_film = result.scalar_one_or_none()
    if not db_film:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(db_film)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_film(movie_id: int, movie: MoviePatchSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db_movie.name = movie.name if movie.name is not None else db_movie.name
    db_movie.date = movie.date if movie.date is not None else db_movie.date
    db_movie.score = movie.score if movie.score is not None else db_movie.score
    db_movie.overview = movie.overview if movie.overview is not None else db_movie.overview
    db_movie.status = movie.status if movie.status is not None else db_movie.status
    db_movie.budget = movie.budget if movie.budget is not None else db_movie.budget
    db_movie.revenue = movie.revenue if movie.revenue is not None else db_movie.revenue

    await db.commit()
    await db.refresh(db_movie)
    return {"detail": "Movie updated successfully."}


async def attach_entities(entities, model: Type[Base], db: AsyncSession):
    if not entities:
        return []

    existing_entities = await db.execute(
        select(model).where(model.name.in_(entities))
    )
    entity_dict = {e.name: e for e in existing_entities.scalars().all()}

    result = []
    for entity_name in entities:
        if entity_name not in entity_dict:
            entity_instance = model(name=entity_name)
        else:
            entity_instance = entity_dict[entity_name]
        db.add(entity_instance)
        result.append(entity_instance)
    await db.flush(result)
    return result
