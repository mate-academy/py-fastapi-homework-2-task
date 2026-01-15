import datetime
from math import ceil
from fastapi import Request


from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select, func, desc

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import GenreModel, CountryModel, ActorModel, LanguageModel

from schemas.movies import MovieListResponseSchema, MovieCreate, MovieDetailSchema, MovieUpdate

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
)
async def get_movies(
    request: Request,
    db: AsyncSession = Depends(get_db,),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    offset = (page - 1) * per_page
    limit = per_page

    result = await db.execute(select(func.count(MovieModel.id)))
    total_items = result.scalar()
    total_items = int(total_items)
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    get_movie = (select(MovieModel).order_by(desc(MovieModel.id))
                 .offset(offset).limit(limit))
    result = await db.execute(get_movie)
    movies = result.scalars().all()
    total_pages = ceil(total_items / per_page)
    prev_page = None
    next_page = None
    base_url = request.url_for("get_movies")
    if page > 1:
        prev_page = f"{base_url}?page={page - 1}&per_page={per_page}"

    if page < total_pages:
        next_page = f"{base_url}?page={page + 1}&per_page={per_page}"

    if len(movies) == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )

@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201,)
async def create_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):


    result = await db.execute(select(MovieModel).where(
        MovieModel.name == movie.name, MovieModel.date == movie.date))
    exists = result.scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409,
                            detail=f"A movie with the name '{exists.name}'"
                                   f" and release date '{exists.date}' already exists.")
    stmt = select(CountryModel).where(CountryModel.code == movie.country)
    result = await db.execute(stmt)
    country = result.scalar_one_or_none()

    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)

    genre_objs = []
    for g in movie.genres:
        stmt = select(GenreModel).where(GenreModel.name == g)
        result = await db.execute(stmt)
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=g)
            db.add(genre)

        genre_objs.append(genre)
    actors_objs = []
    for a in movie.actors:
        stmt = select(ActorModel).where(ActorModel.name == a)
        result = await db.execute(stmt)
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=a)
            db.add(actor)

        actors_objs.append(actor)
    language_objs = []
    for l in movie.languages:
        stmt = select(LanguageModel).where(LanguageModel.name == l)
        result = await db.execute(stmt)
        lang = result.scalar_one_or_none()
        if not lang:
            lang = LanguageModel(name=l)
            db.add(lang)

        language_objs.append(lang)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        country=country,
        genres=genre_objs,
        actors=actors_objs,
        languages=language_objs,
        score=movie.score,
        budget=movie.budget,
        revenue=movie.revenue,
        overview=movie.overview,
        status=movie.status,
    )
    if len(new_movie.name) > 255:
        raise HTTPException(status_code=400, detail="Movie name is too long.")
    if new_movie.score < 0 or new_movie.score > 100:
        raise HTTPException(status_code=400,
                            detail="Movie score must be between 0 and 100.")
    if new_movie.date > (datetime.date.today() + datetime.timedelta(days=366)):
        raise HTTPException(status_code=400,
                            detail="Date cannot be more than one year in the future")
    if new_movie.budget < 0 or new_movie.revenue < 0:
        raise HTTPException(status_code=400,
                            detail="Revenue and budget cannot be less than zero.")

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return MovieDetailSchema.model_validate(new_movie)

@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie_db = select(MovieModel).options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        ).where(MovieModel.id == movie_id)
    result = await db.execute(movie_db)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")
    return MovieDetailSchema.model_validate(movie)

@router.patch("/movies/{movie_id}/",

              )
async def update_movie(movie_id: int,
                       movie: MovieUpdate,
                       db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    movie_to_update = result.scalar_one_or_none()
    if not movie_to_update:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")
    if movie.name:
        if len(movie.name) > 255:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie_to_update.name = movie.name

    if movie.date:
        if movie.date > (datetime.date.today() + datetime.timedelta(days=366)):
            raise HTTPException(status_code=400,
                                detail="Invalid input data.")
        movie_to_update.date = movie.date

    if movie.score:
        if not 0 <= movie.score <= 100:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie_to_update.score = movie.score

    if movie.overview:
        movie_to_update.overview = movie.overview

    if movie.status:
        status_ = ("Released", "Post Production", "In Production")
        if movie.status not in status_:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie_to_update.status = movie.status

    if movie.budget:
        if movie.budget < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie_to_update.budget = movie.budget
    if movie.revenue:
        if movie.revenue < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie_to_update.revenue = movie.revenue

    await db.commit()
    await db.refresh(movie_to_update)
    return {"detail": "Movie updated successfully."}

@router.delete("/movies/{movie_id}/",
               status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return None
