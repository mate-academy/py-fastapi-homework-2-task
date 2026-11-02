from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieCreate, MovieDetailSchema, MovieUpdate

router = APIRouter()

@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(page:int =  Query(1, ge = 1), per_page: int = Query(10, ge=1, le=20), db: AsyncSession = Depends(get_db)):
    movies_count = await db.execute(select(func.count(MovieModel.id)).select_from(MovieModel))
    movies_count = movies_count.scalar()

    if not movies_count or movies_count == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = movies_count // per_page + 1
    offset = (page - 1) * per_page

    movies = await db.execute(select(MovieModel).offset(offset).limit(per_page).order_by(MovieModel.id.desc()))
    movies = movies.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None


    return MovieListResponseSchema(
        movies=movies,
        next_page=next_page,
        prev_page=prev_page,
        total_pages=total_pages,
        total_items=movies_count
    )

async def get_or_create_inner_instances(model_class, data: list[str],  db: AsyncSession) -> list:
    item_instants_list = []

    for item_name in data:
        stmt_items = select(model_class).where(getattr(model_class, "name") == item_name)
        result = await db.execute(stmt_items)
        item = result.scalars().first()


        if not item:
            try:
                item = model_class(name=item_name)
                db.add(item)
                await db.flush()
            except IntegrityError:
                await db.rollback()
                item = await db.execute(stmt_items)
                item = item.scalars().first()
        item_instants_list.append(item)

    return item_instants_list

@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movies(movie: MovieCreate, db: AsyncSession = Depends(get_db)):

    db_same_movie = await db.execute(select(MovieModel).where(MovieModel.name == movie.name and MovieModel.date == movie.date))
    db_same_movie = db_same_movie.scalar_one_or_none()
    if db_same_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    genre_list = await get_or_create_inner_instances(GenreModel,  movie.genres, db)
    actor_list = await get_or_create_inner_instances(ActorModel, movie.actors, db)
    languages_list = await get_or_create_inner_instances(LanguageModel, movie.languages, db)

    stmt_country = select(CountryModel).where(CountryModel.code == movie.country)
    result_country = await db.execute(stmt_country)
    country = result_country.scalars().first()

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
        genres=genre_list,
        actors=actor_list,
        languages=languages_list,
        country=country
    )
    db.add(new_movie)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    )
    movie = await db.execute(stmt)
    movie = movie.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie

@router.delete("/movies/{movie_id}/", response_model=None, status_code=204)
async def delete_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_film = result.scalar_one_or_none()
    if not db_film:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(db_film)
    await db.commit()
    return

@router.patch("/movies/{movie_id}/")
async def update_movie_by_id(movie_id: int, payload: dict = Body(), db: AsyncSession = Depends(get_db)):
    try:
        movie_data = MovieUpdate(**payload)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    stmt = select(MovieModel).where(MovieModel.id == movie_id).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    )
    result = await db.execute(stmt)
    db_film = result.unique().scalar_one_or_none()
    if not db_film:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update_data.items():
        setattr(db_film, key, value)

    try:
        await db.commit()
        await db.refresh(db_film)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the same name and release date already exists."
        )

    return {"detail": "Movie updated successfully."}
